# test_cron_full.py
"""
실무자용 CRON + DB + 로그 통합 테스트
- FAST/FULL 모드 지원
- 반복 실행 및 CRON 시뮬레이션 가능
"""

import time
import pymysql
import os
from datetime import datetime
from src.rss import run_cron_job

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
# 2. 테스트 반복 설정
# =========================
ITERATIONS = 3         # 반복 횟수 기본값
INTERVAL = 5 * 60      # FULL 모드 기본 CRON 간격: 5분

# =========================
# 3. FAST 모드 체크
# =========================
FAST_MODE = os.getenv("TEST_MODE") == "FAST"
INTERVAL = 1 if FAST_MODE else INTERVAL  # FAST 모드면 1초

# =========================
# 4. 반복 테스트 실행
# =========================
for i in range(1, ITERATIONS + 1):
    print(f"\n=== [{i}/{ITERATIONS}] CRON 시뮬레이션 실행: {datetime.now()} ===")

    # 4-1. CRON 함수 실행
    run_cron_job()

    # 4-2. DB 상태 확인
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
        SELECT link, COUNT(*)
        FROM articles_old
        GROUP BY link
        HAVING COUNT(*) > 1;
    """)
    duplicates = cur.fetchall()
    conn.close()

    # 4-3. 결과 출력
    print(f"\n[DB 상태] articles_old: {archived_count}, articles: {original_count}")
    if duplicates:
        print("중복 링크 발견:")
        for link, cnt in duplicates:
            print(f"{link} - {cnt}건")
    else:
        print("중복 링크 없음 ✅")

    # 4-4. 로그 확인
    print("\n[최근 로그 (마지막 20줄)]")
    try:
        with open("logs/app.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.strip())
    except FileNotFoundError:
        print("로그 파일 없음: logs/app.log")

    # 4-5. 다음 반복 전 대기
    if i < ITERATIONS:
        wait_time = INTERVAL
        print(f"\n다음 반복까지 {wait_time if FAST_MODE else wait_time//60} {'초' if FAST_MODE else '분'} 대기...\n")
        time.sleep(INTERVAL)

print("\n=== 테스트 종료 ===")

