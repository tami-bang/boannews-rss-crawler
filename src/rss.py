# src/rss.py
"""
RSS 수집 및 파싱 + DB 저장
"""
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import feedparser
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List
import warnings
from datetime import datetime
from .db import get_connection, save_article

# XML을 HTML parser로 읽는 경고 무시
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

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

def parse_rss(rss_url: str):
    feed = feedparser.parse(rss_url, agent="Mozilla/5.0")
    if feed.bozo:
        logging.warning(f"RSS 파싱 경고: {feed.bozo_exception}")
    return feed

def fetch_entries(index_url: str) -> List:
    """RSS 읽고 DB 저장까지 처리"""
    session = make_session()
    conn = get_connection()
    if not conn:
        logging.error("DB 연결 실패. RSS 수집 중단.")
        return []

    try:
        logging.info("RSS 목록 페이지 접근 중...")
        rss_url = find_full_rss_url(index_url, session)
        logging.info("RSS 파싱 중...")
        feed = parse_rss(rss_url)
        logging.info(f"entries 수집: {len(feed.entries)}")

        for entry in feed.entries:
            article = {
                'title': entry.title,
                'link': entry.link,
                'published': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                'summary': entry.summary if hasattr(entry, 'summary') else None,
                'source': 'boannews',
                'category': getattr(entry, 'tags', None),  # 필요시 태그 처리
                'author': getattr(entry, 'author', None)
            }
            save_article(conn, article)
        return feed.entries
    except Exception as e:
        logging.exception("RSS 수집 중 오류 발생")
        return []
    finally:
        conn.close()
