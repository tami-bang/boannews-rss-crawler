# main.py
import logging
from logging_config import setup_logging
from src import fetch_entries

if __name__ == "__main__":
    setup_logging()
    RSS_INDEX_URL = "https://www.boannews.com/custom/news_rss.asp"

    try:
        entries = fetch_entries(RSS_INDEX_URL)
        for i, entry in enumerate(entries, start=1):
            print(f"{i:2}) {entry.link}  {entry.title}")
    except Exception as e:
        logging.exception("실행 중 오류 발생")
