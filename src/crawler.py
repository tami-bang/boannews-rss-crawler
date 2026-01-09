# 보안 뉴스 메인 페이지에서 rss 페이지를 탐색하여 수집하고자 하는 rss를 선택, 파싱하는 것까지
# 하나의 작업으로 연결해보세요.
import requests
from bs4 import BeautifulSoup
import feedparser
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List

# ----------------- 로깅 설정 -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------- HTTP 세션 설정 (Retry 포함) -----------------
def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

#1. RSS 목록 페이지에서 전체기사 RSS 링크 탐색
def find_full_rss_url(index_url: str, session: requests.Session) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = session.get(index_url, headers=headers, timeout=10)
    r.raise_for_status()
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")

    for inp in soup.select("input[value]"):
        val = inp.get("value")
        if val and val.lower().endswith(".xml") and "rss" in val.lower():
            logging.info(f"RSS URL 발견: {val}")
            return val

    raise RuntimeError("RSS XML 링크를 찾지 못했습니다.")

#2. RSS 파싱
def parse_rss(rss_url: str):
    feed = feedparser.parse(rss_url, agent="Mozilla/5.0")

    if feed.bozo:
        logging.warning(f"RSS 파싱 경고: {feed.bozo_exception}")

    return feed

#3. 전체 흐름 연결
def main() -> List:
    RSS_INDEX_URL = "https://www.boannews.com/custom/news_rss.asp"
    session = make_session()

    try:
        logging.info("RSS 목록 페이지 접근 중...")
        rss_url = find_full_rss_url(RSS_INDEX_URL, session)

        logging.info("RSS 파싱 중...")
        feed = parse_rss(rss_url)

        logging.info(f"entries: {len(feed.entries)}")

        for i, entry in enumerate(feed.entries, start=1):
            print(f"{i:2}) {entry.link}  {entry.title}")

        return feed.entries

    except requests.exceptions.RequestException as e:
        logging.error(f"네트워크 오류: {e}")
    except RuntimeError as e:
        logging.error(f"데이터 처리 오류: {e}")
    except Exception as e:
        logging.exception("알 수 없는 오류 발생")

    return []

if __name__ == "__main__":
    main()
