# tests/helpers.py
"""
공용 헬퍼 모듈
- DB 접속
- CRON 시뮬레이션 반복용 설정
- 로그 확인
- FAST/FULL 모드 처리
"""

import os
import pymysql

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

def get_connection():
    """DB 연결 반환"""
    return pymysql.connect(**DB)

def get_db_counts():
    """
    DB 상태 확인
    - articles_old 아카이브 건수
    - articles 원본 남은 건수
    - articles_old 중복 링크 확인
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM articles_old WHERE fetched_at <= NOW() - INTERVAL 1 DAY;")
    archived_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM articles WHERE fetched_at <= NOW() - INTERVAL 1 DAY;")
    original_count = cur.fetchone()[0]

    cur.execute("""
        SELECT link, COUNT(*) FROM articles_old
        GROUP BY link
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()

    conn.close()
    return archived_count, original_count, duplicates

def get_recent_logs(lines=20):
    """최근 로그(lines 수만큼) 읽기"""
    log_file = "logs/app.log"
    if not os.path.exists(log_file):
        return []
    with open(log_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()[-lines:]]

# =========================
# 2. FAST/FULL 모드 설정
# =========================
FAST_MODE = os.getenv("TEST_MODE") == "FAST"
INTERVAL = 1 if FAST_MODE else 5*60  # FAST=1초, FULL=5분
ITERATIONS = 3  # 반복 횟수 기본값

