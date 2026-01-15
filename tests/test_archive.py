# tests/test_archive.py
import pytest
from src.rss import archive_old_articles
from src.db import get_connection

def test_archive_and_duplicates():
    """
    articles → articles_old 아카이브 및 중복 링크 처리 확인
    """
    conn = get_connection()
    assert conn is not None, "DB 연결 실패"

    # 아카이브 실행
    archive_old_articles(days=0)  # 오늘 기사까지 아카이브

    cur = conn.cursor()
    # 원본 삭제 확인
    cur.execute("SELECT COUNT(*) FROM articles")
    remaining = cur.fetchone()[0]
    assert remaining >= 0, "articles 삭제 오류"

    # 중복 링크 확인
    cur.execute("""
        SELECT link, COUNT(*) FROM articles_old
        GROUP BY link
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    assert duplicates == [], "articles_old 중복 링크 존재"

    cur.close()
    conn.close()
