# check_cron_full_and_repeat.py
"""
통합 CRON 점검 스크립트
- 운영용 모드 (실무자용): 1회 실행으로 RSS 수집 + 아카이브 + 중복/수집 건수 확인
- 테스트용 모드 (개발/자동화용): 반복 실행 가능, DB 상태 자동 검증
- 사용법:
    python check_cron_full_and_repeat.py --mode run_once
    python check_cron_full_and_repeat.py --mode repeat --repeat 3 --delay 10
"""

import asyncio
import logging
import time
import argparse
from datetime import datetime, timedelta
from src.db import get_connection, save_article
from src.rss import fetch_all_entries, archive_old_articles, run_cron_job

# ===========================================================
# 0. 로깅 설정
# ===========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ===========================================================
# 1. DB 상태 확인 (공통, 운영/테스트 모두 사용)
# ===========================================================
def check_db_summary():
    """
    1. articles_old에 아카이브된 기사 수 확인
    2. articles에 남아있는 원본 기사 수 확인
    3. articles_old에서 중복 링크 확인
    """
    conn = get_connection()
    if not conn:
        print("[ERROR] DB 연결 실패")
        return

    cursor = conn.cursor()
    cutoff_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    try:
        # articles_old 아카이브 확인
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM articles_old WHERE fetched_at <= %s", (cutoff_str,)
        )
        articles_old_count = cursor.fetchone()[0]

        # articles 원본 확인
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM articles WHERE fetched_at <= %s", (cutoff_str,)
        )
        articles_count = cursor.fetchone()[0]

        # articles_old 중복 링크 확인
        cursor.execute(
            "SELECT link, COUNT(*) AS cnt FROM articles_old GROUP BY link HAVING COUNT(*) > 1"
        )
        duplicates = cursor.fetchall()

        print(f"▶ 아카이브된 articles_old 기사 수 (1일 이상): {articles_old_count}")
        print(f"▶ 원본 articles 기사 수 (1일 이상): {articles_count}")
        if duplicates:
            print(f"▶ 중복 링크 발견: {len(duplicates)}건")
            for link, count in duplicates:
                print(f"  - {link} : {count}회")
        else:
            print("▶ 중복 링크 없음")

    finally:
        cursor.close()
        conn.close()


# ===========================================================
# 2. 운영용 모드 (실무자용)
# ===========================================================
def run_once_mode():
    """
    운영용 1회 실행
    - RSS 수집 + DB 저장
    - articles_old 아카이브 + 중복 확인
    """
    print(f"\n=== 운영용 CRON 점검 시작: {datetime.now()} ===\n")

    # 1) 아카이브 실행
    archive_old_articles(days=1)

    # 2) RSS 수집 실행
    asyncio.run(fetch_all_entries())

    # 3) DB 상태 확인
    check_db_summary()

    print(f"\n=== 운영용 CRON 점검 종료: {datetime.now()} ===\n")


# ===========================================================
# 3. 테스트용 모드 (개발/자동화용)
# ===========================================================
def run_repeat_mode(repeat=3, delay_sec=10):
    """
    테스트용 반복 실행
    - 반복 횟수, 반복 간 대기 시간 조정 가능
    """
    for i in range(repeat):
        print(f"\n========== 반복 테스트 {i+1}/{repeat} ==========")
        print("1️⃣ CRON 작업 실행 중 (아카이브 + RSS 수집)...")
        run_cron_job()
        print("2️⃣ DB 상태 확인 중...")
        check_db_summary()
        if i < repeat - 1:
            print(f"⏱ {delay_sec}초 대기 후 다음 반복 실행")
            time.sleep(delay_sec)


# ===========================================================
# 4. 메인 실행
# ===========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CRON 점검 스크립트")
    parser.add_argument("--mode", choices=["run_once", "repeat"], default="run_once",
                        help="실행 모드: run_once=운영용 1회 실행, repeat=테스트용 반복 실행")
    parser.add_argument("--repeat", type=int, default=3, help="반복 실행 횟수 (repeat 모드)")
    parser.add_argument("--delay", type=int, default=10, help="반복 실행 간 대기 시간 초 (repeat 모드)")

    args = parser.parse_args()

    if args.mode == "run_once":
        run_once_mode()
    else:
        run_repeat_mode(repeat=args.repeat, delay_sec=args.delay)

