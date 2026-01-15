# src/rss.py
"""
BoanNews RSS 수집 + DB 저장 + 아카이브
- 발행일 안전 처리 포함
- articles_old로 아카이브 자동 이동
- 중복 링크 발생 시 업데이트 처리
- CRON용 실행 함수 포함
"""

import asyncio
import aiohttp
import feedparser
from bs4 import XMLParsedAsHTMLWarning
import logging
from typing import List
import warnings
from datetime import datetime, timedelta
from charset_normalizer import from_bytes
from .db import get_connection, save_article

# ===========================================================
# 0. 경고 무시 설정
# ===========================================================
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ===========================================================
# 1. RSS 인덱스 및 fallback
# ===========================================================
RSS_INDEX_PAGES = [
    "http://www.boannews.com",
    "http://www.boannews.com/media"
]

RSS_FALLBACK = [
    "http://www.boannews.com/media/news_rss.xml?mkind=1",
    "http://www.boannews.com/media/news_rss.xml?mkind=2",
    "http://www.boannews.com/media/news_rss.xml?mkind=3",
    "http://www.boannews.com/media/news_rss.xml?mkind=4",
    "http://www.boannews.com/media/news_rss.xml?mkind=5",
    "http://www.boannews.com/media/news_rss.xml?kind=1",
    "http://www.boannews.com/media/news_rss.xml?kind=2",
    "http://www.boannews.com/media/news_rss.xml?kind=3",
    "http://www.boannews.com/media/news_rss.xml?kind=4",
    "http://www.boannews.com/media/news_rss.xml?kind=5",
    "http://www.boannews.com/media/news_rss.xml?kind=6",
    "http://www.boannews.com/media/news_rss.xml?skind=2",
    "http://www.boannews.com/media/news_rss.xml?skind=3",
    "http://www.boannews.com/media/news_rss.xml?skind=5",
    "http://www.boannews.com/media/news_rss.xml?skind=6",
    "http://www.boannews.com/media/news_rss.xml?skind=7"
]

# ===========================================================
# 2. 로깅 설정
# ===========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ===========================================================
# 3. 유틸리티 함수
# ===========================================================
def safe_get_entry_value(entry, attr: str):
    """RSS entry 속성 안전 접근"""
    return getattr(entry, attr, None)

def parse_published(entry) -> datetime:
    """
    RSS entry에서 발행일 추출
    - published_parsed 존재하면 사용
    - 없으면 updated_parsed 사용
    - 둘 다 없으면 현재 시각
    """
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
    except Exception as e:
        logging.warning(f"발행일 파싱 실패: {getattr(entry, 'link', '')} - {e}")
    return datetime.now()

# ===========================================================
# 4. RSS 인덱스 탐색
# ===========================================================
async def discover_all_rss(session: aiohttp.ClientSession) -> List[str]:
    """RSS 인덱스 페이지를 탐색하고 RSS URL 수집"""
    rss_urls = set()
    headers = {"User-Agent": "Mozilla/5.0"}
    from bs4 import BeautifulSoup

    for page in RSS_INDEX_PAGES:
        try:
            async with session.get(page, headers=headers, timeout=10) as resp:
                text_bytes = await resp.read()
                enc_result = from_bytes(text_bytes).best()
                text = str(enc_result) if enc_result else text_bytes.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(text, "html.parser")
                for tag in soup.select("a[href], link[href], input[value]"):
                    url = tag.get("href") or tag.get("value")
                    if url and "news_rss.xml" in url.lower():
                        if url.startswith("/"):
                            url = "http://www.boannews.com" + url
                        rss_urls.add(url)
        except Exception as e:
            logging.warning(f"RSS 인덱스 탐색 실패: {page} - {e}")

    if not rss_urls:
        logging.warning("자동 RSS 탐색 실패, fallback 사용")
        rss_urls.update(RSS_FALLBACK)

    logging.info(f"발견된 RSS 피드 수: {len(rss_urls)}")
    return list(rss_urls)

# ===========================================================
# 5. RSS 파싱
# ===========================================================
async def parse_rss(session: aiohttp.ClientSession, rss_url: str) -> feedparser.FeedParserDict:
    """RSS 요청 후 feedparser로 파싱"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(rss_url, headers=headers, timeout=10) as resp:
            content = await resp.read()
            enc_result = from_bytes(content).best()
            text = str(enc_result) if enc_result else content.decode('utf-8', errors='ignore')
            feed = feedparser.parse(text)
            if feed.bozo:
                logging.warning(f"RSS 파싱 경고: {rss_url} - {feed.bozo_exception}")
            if not hasattr(feed, 'entries'):
                feed.entries = []
            return feed
    except Exception as e:
        logging.exception(f"RSS 요청/파싱 실패: {rss_url} - {e}")
        return feedparser.FeedParserDict(entries=[])

# ===========================================================
# 6. 단일 RSS 수집
# ===========================================================
async def fetch_single_rss(session: aiohttp.ClientSession, rss_url: str, conn=None) -> List[dict]:
    """단일 RSS 수집 후 DB 저장"""
    feed = await parse_rss(session, rss_url)
    entries_list = []

    for entry in getattr(feed, 'entries', []):
        link = safe_get_entry_value(entry, 'link')
        if not link:
            continue

        published = parse_published(entry)

        article = {
            'title': safe_get_entry_value(entry, 'title'),
            'link': link,
            'published': published,
            'summary': safe_get_entry_value(entry, 'summary'),
            'source': 'boannews',
            'category': rss_url,
            'author': safe_get_entry_value(entry, 'author')
        }

        if conn:
            save_article(conn, article)  # DB 저장: 중복 링크 발생 시 업데이트 포함

        entries_list.append(article)

    return entries_list

# ===========================================================
# 7. 전체 RSS 수집
# ===========================================================
async def fetch_all_entries(conn=None) -> List[dict]:
    """모든 RSS 수집 및 중복 제거 후 DB 저장"""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
        if not conn:
            logging.error("DB 연결 실패. 전체 RSS 수집 중단.")
            return []

    all_entries = []
    seen_links = set()
    async with aiohttp.ClientSession() as session:
        rss_urls = await discover_all_rss(session)
        tasks = [fetch_single_rss(session, url, conn) for url in rss_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for entries in results:
        if isinstance(entries, Exception):
            logging.error(f"RSS 처리 중 예외 발생: {entries}")
            continue
        for article in entries:
            if article['link'] in seen_links:
                continue
            seen_links.add(article['link'])
            all_entries.append(article)

    if close_conn and conn:
        conn.close()

    logging.info(f"총 수집 기사 수: {len(all_entries)}")
    return all_entries

# ===========================================================
# 8. articles 아카이브
# ===========================================================
def archive_old_articles(days=1):
    """
    1. articles_old로 이동 (중복 링크 발생 시 업데이트 처리)
    2. 아카이브 완료된 행만 articles에서 삭제
    3. 트랜잭션으로 묶어 실패 시 rollback
    """
    conn = get_connection()
    if not conn:
        logging.error("DB 연결 실패. 아카이브 중단.")
        return

    cursor = conn.cursor()
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    try:
        # =======================================================
        # 1. 이동할 대상 선택
        # =======================================================
        cursor.execute("""
            SELECT id, title, link, published, summary, source, category, author, fetched_at
            FROM articles
            WHERE fetched_at <= %s
        """, (cutoff_str,))
        rows_to_archive = cursor.fetchall()
        if not rows_to_archive:
            logging.info("아카이브 대상 없음")
            return

        # =======================================================
        # 2. articles_old에 INSERT + 중복 발생 시 UPDATE
        # =======================================================
        for row in rows_to_archive:
            cursor.execute("""
                INSERT INTO articles_old (id, title, link, published, summary, source, category, author, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    summary = VALUES(summary),
                    published = VALUES(published),
                    category = VALUES(category),
                    author = VALUES(author)
            """, row)

        # =======================================================
        # 3. 아카이브 완료된 행만 원본 삭제
        # =======================================================
        archived_ids = [row[0] for row in rows_to_archive]  # id 기준
        if archived_ids:
            format_strings = ','.join(['%s'] * len(archived_ids))
            cursor.execute(f"DELETE FROM articles WHERE id IN ({format_strings})", archived_ids)

        # =======================================================
        # 4. 커밋
        # =======================================================
        conn.commit()
        logging.info(f"{len(rows_to_archive)}건 아카이브 완료 (articles → articles_old)")

    except Exception as e:
        conn.rollback()
        logging.error(f"아카이브 실패: {e}")
    finally:
        cursor.close()
        conn.close()


# ===========================================================
# 9. CRON용 실행 함수
# ===========================================================
def run_cron_job():
    """
    1시간마다 실행
    1. 1일 이상 지난 기사 아카이브
    2. RSS 수집
    """
    archive_old_articles(days=1)
    asyncio.run(fetch_all_entries())

# ===========================================================
# 10. 개발용 실행 예시
# ===========================================================
if __name__ == "__main__":
    run_cron_job()

