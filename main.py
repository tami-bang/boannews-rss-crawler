# main.py
import logging
from logging_config import setup_logging
from src.rss import fetch_entries
from src.rss import save_article
from datetime import datetime
from src.db import get_connection

if __name__ == "__main__":
    setup_logging()
    RSS_INDEX_URL = "http://www.boannews.com/media/news_rss.xml"

    try:
        entries = fetch_entries(RSS_INDEX_URL)
        for i, entry in enumerate(entries, start=1):
            article = {
                'title': entry.title,
                'link': entry.link,
                'published': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                'summary': getattr(entry, 'summary', None),
                'source': 'boannews',
            }
            save_article(article)
            print(f"{i:2}) 저장 완료: {article['title']}")
    except Exception as e:
        logging.exception("실행 중 오류 발생")

conn = get_connection()
if conn:
    print("DB 연결 성공!")
    conn.close()
else:
    print("DB 연결 실패")