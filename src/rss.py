# rss.py
"""
RSS 수집 및 파싱
RSS URL 검색 + RSS 파싱 + feed 반환
"""
import requests
from bs4 import BeautifulSoup
import feedparser
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List

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
    """전체 흐름 연결"""
    session = make_session()
    try:
        logging.info("RSS 목록 페이지 접근 중...")
        rss_url = find_full_rss_url(index_url, session)
        logging.info("RSS 파싱 중...")
        feed = parse_rss(rss_url)
        logging.info(f"entries: {len(feed.entries)}")
        return feed.entries
    except Exception as e:
        logging.exception("RSS 수집 중 오류 발생")
        return []
