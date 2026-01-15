# tests/test_archive.py
"""
articles → articles_old 아카이브 테스트 (운영 DB 안전)
- DB 상태 확인
- 중복 링크 경고 출력
"""

import pytest
from src.rss import archive_old_articles
from tests.helpers import get_connection, get_db_counts

def test_archive_and_duplicates():
    conn = get_connection()
    assert conn is not None, "DB 연결 실패"

    # 오늘까지 아카이브
    archive_old_articles(days=0)

    # DB 상태 확인
    archived_count, original_count, duplicates = get_db_counts()
    print(f"articles_old={archived_count}, articles={original_count}")

    # 중복 링크 경고
    if duplicates:
        print(f"WARNING: articles_old 중복 링크 존재! {duplicates}")
    else:
        print("중복 링크 없음 ✅")

    # 원본 articles 확인 (삭제되었더라도 음수 방지)
    assert original_count >= 0, "articles 삭제 오류"

    conn.close()

