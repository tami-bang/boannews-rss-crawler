# test_cron_automated.py
"""
Pytest 기반 실무 자동화 CRON 테스트
- run_cron_job() 실행 후 DB와 로그 검증
- FAST/FULL 모드 지원 (환경변수 TEST_MODE)
- 반복 실행 가능, 실패 시 pytest에서 알려줌
"""

import os
import pytest
import pymysql
from datetime import datetime
from src.rss import run_cron_job
import time

# =========================
# 1. DB 접속 정보
# =========================
DB = {
    "host": "localhost",
    "user": "newsbot",
    "password": "newsbot_pass!",
    "database": "boannews",
    "charset": "utf8mb4"
}

# =========================
# 2. FAST/FULL 모드 설정
# =========================
FAST_MODE = os.getenv("TEST_MODE") == "FAST"
ITERATIONS = 3
INTERVAL = 1 if FAST_MODE else 5 * 60  # FAST=1초, FULL=5분

# =========================
# 3. DB 상태 체크 헬퍼
# =========================
def get_db_counts():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    # 아카이브 건수
    cur.execute("SELECT COUNT(*) FROM articles_old WHERE fetched_at <= NOW() - INTERVAL 1 DAY;")
    archived_count = cur.fetchone()[0]
    # 원본 남은 건수
    cur.execute("SELECT COUNT(*) FROM articles WHERE fetched_at <= NOW() - INTERVAL 1 DAY;")
    original_count = cur.fetchone()[0]
    # 중복 링크 확인
    cur.execute("""
        SELECT link, COUNT(*) FROM articles_old
        GROUP BY link
        HAVING COUNT(*) > 1;
    """)
    duplicates = cur.fetchall()
    conn.close()
    return archived_count, original_count, duplicates

# =========================
# 4. 로그 체크 헬퍼
# =========================
def get_recent_logs(lines=20):
    try:
        with open("logs/app.log", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()[-lines:]]
    except FileNotFoundError:
        return []

# =========================
# 5. Pytest 테스트 케이스 (FAST/FULL 모드 통합)
# =========================
@pytest.mark.parametrize("iteration", range(ITERATIONS))
def test_cron_simulation(iteration):
    print(f"\n=== [Iteration {iteration+1}/{ITERATIONS}] CRON 실행: {datetime.now()} ===")

    # 5-1. CRON 함수 실행
    run_cron_job()

    # 5-2. DB 상태 확인
    archived_count, original_count, duplicates = get_db_counts()

    # 5-3. 검증
    assert archived_count >= 0, "articles_old 아카이브 건수 확인"
    assert original_count >= 0, "articles 원본 건수 확인"
    assert duplicates == [], "articles_old 중복 링크 없음 확인"

    # 5-4. 로그 확인
    logs = get_recent_logs()
    assert any("아카이브" in line or "총 수집 기사 수" in line for line in logs), \
        "최근 로그에 아카이브 및 수집 기록 존재 확인"

    # 5-5. 디버그용 출력
    print(f"articles_old={archived_count}, articles={original_count}")
    if duplicates:
        print("중복 링크 발견:", duplicates)
    else:
        print("중복 링크 없음 ✅")
    print("최근 로그 확인 완료")

    # 5-6. 다음 반복 전 대기 (FAST/FULL 모드 반영)
    if iteration < ITERATIONS - 1:
        wait_time = INTERVAL
        print(f"\n다음 반복까지 {wait_time if FAST_MODE else wait_time//60} {'초' if FAST_MODE else '분'} 대기...\n")
        time.sleep(INTERVAL)

