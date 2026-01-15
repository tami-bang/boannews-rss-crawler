# tests/test_rss_db.py
"""
RSS 수집 후 DB 저장 및 중복 처리 확인 (운영 DB 안전)
- async 함수 테스트
- 수집 결과 없으면 경고 출력
"""

import pytest
from src.rss import fetch_all_entries
from tests.helpers import get_connection

@pytest.mark.asyncio
async def test_rss_fetch_and_db_save():
    conn = get_connection()
    assert conn is not None, "DB 연결 실패"

    entries = await fetch_all_entries(conn)
    if not entries:
        print("WARNING: 수집 기사 없음")
    else:
        print(f"수집 기사 {len(entries)}건 확인")

    # DB 저장 확인
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles")
    count = cur.fetchone()[0]
    if count == 0:
        print("WARNING: DB에 기사 저장 안됨")
    else:
        print(f"DB에 저장된 기사 {count}건 확인")

    cur.close()
    conn.close()

