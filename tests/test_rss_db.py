# tests/test_rss_db.py
import pytest
import asyncio
from src.rss import fetch_all_entries
from src.db import get_connection

@pytest.mark.asyncio
async def test_rss_fetch_and_db_save():
    """
    RSS 전체 수집 후 DB 저장 및 중복 처리 확인
    """
    conn = get_connection()
    assert conn is not None, "DB 연결 실패"

    entries = await fetch_all_entries(conn)
    assert isinstance(entries, list), "수집 결과 리스트 아님"
    assert len(entries) > 0, "수집 기사 없음"

    # DB 삽입 확인
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles")
    count = cur.fetchone()[0]
    assert count > 0, "DB에 기사 저장 안됨"

    cur.close()
    conn.close()

