# main.py
import logging
from logging_config import setup_logging
from src.rss import fetch_entries
from src.db import get_connection

if __name__ == "__main__":
    setup_logging(mode="dev")  # 개발용: 콘솔+파일, DEBUG 출력

    RSS_INDEX_URL = "http://www.boannews.com/media/news_rss.xml"

    # DB 연결
    conn = get_connection()
    if not conn:
        logging.error("DB 연결 실패!")
        exit(1)
    logging.info("DB 연결 성공!")

    try:
        # RSS 수집 + DB 저장
        entries = fetch_entries(RSS_INDEX_URL, conn)
        for i, entry in enumerate(entries, start=1):
            logging.info(f"{i:2}) 수집 완료: {entry.title}")
    except Exception:
        logging.exception("실행 중 오류 발생")
    finally:
        conn.close()
        logging.info("DB 연결 종료")
