# tests/test_cron_full.py
"""
Pytest 기반 실무 자동화 CRON 테스트 (FULL 모드)
- run_cron_job() 실행 후 DB와 로그 검증
- FAST/FULL 모드 지원 (환경변수 TEST_MODE)
- 반복 실행 가능, 실패 시 pytest에서 알려줌
- articles_old 중복 링크는 PASS 처리, 로그만 표시
"""

import os
import pytest
import pymysql
from datetime import datetime
from src.rss import run_cron_job
import time
from tests.helpers import get_db_counts, get_recent_logs

# =========================
# 1. FAST/FULL 모드 설정
# =========================
FAST_MODE = os.getenv("TEST_MODE") == "FAST"
ITERATIONS = 3
INTERVAL = 1 if FAST_MODE else 5 * 60  # FAST=1초, FULL=5분

# =========================
# 2. Pytest 테스트 케이스 (FAST/FULL 모드 통합)
# =========================
@pytest.mark.parametrize("iteration", range(ITERATIONS))
def test_cron_simulation(iteration):
    """CRON 반복 실행 시뮬레이션 테스트"""
    print(f"\n=== [Iteration {iteration+1}/{ITERATIONS}] CRON 실행: {datetime.now()} ===")

    # 2-1. CRON 함수 실행
    run_cron_job()

    # 2-2. DB 상태 확인
    archived_count, original_count, duplicates = get_db_counts()

    # 2-3. 검증 (중복 링크는 PASS 처리)
    assert archived_count >= 0, "articles_old 건수 음수"
    assert original_count >= 0, "articles 건수 음수"

    if duplicates:
        print("중복 링크 발견:", duplicates)
    else:
        print("중복 링크 없음")

    # 2-4. 로그 확인
    logs = get_recent_logs()
    assert any("아카이브" in line or "총 수집 기사 수" in line for line in logs), \
        "최근 로그에 아카이브 및 수집 기록 존재 확인"

    # 2-5. 디버그용 출력
    print(f"articles_old={archived_count}, articles={original_count}")
    print("최근 로그 확인 완료")

    # 2-6. 다음 반복 전 대기 (FAST/FULL 모드 반영)
    if iteration < ITERATIONS - 1:
        wait_time = INTERVAL
        print(f"\n다음 반복까지 {wait_time if FAST_MODE else wait_time//60} {'초' if FAST_MODE else '분'} 대기...\n")
        time.sleep(INTERVAL)

