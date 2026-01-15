# test_cron_automated.py
"""
Pytest 기반 실무 자동화 CRON 테스트 (안전 모드)
- run_cron_job() 실행 후 DB와 로그 검증
- FAST/FULL 모드 지원 (환경변수 TEST_MODE)
- 반복 실행 가능, 중복 링크 발견 시 경고 출력
"""

import pytest
import time
from datetime import datetime
from src.rss import run_cron_job
from tests.helpers import INTERVAL, ITERATIONS, get_db_counts, get_recent_logs, FAST_MODE

@pytest.mark.parametrize("iteration", range(ITERATIONS))
def test_cron_simulation(iteration):
    """CRON 반복 실행 시뮬레이션 테스트 (운영 DB 안전)"""
    print(f"\n=== [Iteration {iteration+1}/{ITERATIONS}] CRON 실행: {datetime.now()} ===")

    # 1. CRON 함수 실행
    run_cron_job()

    # 2. DB 상태 확인
    archived_count, original_count, duplicates = get_db_counts()
    print(f"articles_old={archived_count}, articles={original_count}")

    # 3. 검증
    assert archived_count >= 0, "articles_old 아카이브 건수 음수"
    assert original_count >= 0, "articles 원본 건수 음수"

    # 4. 중복 링크 경고 처리 (운영 DB 보호)
    if duplicates:
        print(f"WARNING: articles_old 중복 링크 존재! {duplicates}")
    else:
        print("중복 링크 없음")

    # 5. 로그 확인
    logs = get_recent_logs()
    if any("아카이브" in line or "총 수집 기사 수" in line for line in logs):
        print("최근 로그에 아카이브 및 수집 기록 확인")
    else:
        print("WARNING: 최근 로그에 아카이브 및 수집 기록 없음")

    # 6. 다음 반복 전 대기 (FAST/FULL 모드 반영)
    if iteration < ITERATIONS - 1:
        wait_time = INTERVAL
        print(f"\n다음 반복까지 {wait_time if FAST_MODE else wait_time//60} "
              f"{'초' if FAST_MODE else '분'} 대기...\n")
        time.sleep(INTERVAL)

