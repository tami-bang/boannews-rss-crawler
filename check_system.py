# check_system.py
# ============================================================
# 실무 검증 스크립트
# - RSS 수집 확인
# - DB 저장 확인
# - 로그 확인
# - 메일 테스트
# ============================================================

import pymysql
import subprocess
from datetime import datetime, timedelta
import os

# =========================
# DB 접속 정보
# =========================
DB = {
    "host": "localhost",
    "user": "newsbot",
    "password": "newsbot_pass!",
    "database": "boannews",
    "charset": "utf8mb4"
}

# =========================
# 로그 파일 경로
# =========================
LOG_FILE = "logs/app.log"

# =========================
# 오늘/어제 시간 범위 계산
# =========================
today = datetime.now().date()
yesterday = today - timedelta(days=1)
today_start = datetime.combine(today, datetime.min.time())
yesterday_start = datetime.combine(yesterday, datetime.min.time())
yesterday_end = today_start

# =========================
# DB 연결
# =========================
conn = pymysql.connect(**DB)
cur = conn.cursor()

def check_articles(start, end):
    cur.execute("""
        SELECT COUNT(*) FROM articles
        WHERE fetched_at >= %s AND fetched_at < %s
    """, (start, end))
    count = cur.fetchone()[0]

    cur.execute("""
        SELECT title, category
        FROM articles
        WHERE fetched_at >= %s AND fetched_at < %s
        ORDER BY fetched_at DESC
        LIMIT 3
    """, (start, end))
    sample = cur.fetchall()
    return count, sample

# =========================
# 1. 오늘 수집 기사 확인
# =========================
today_count, today_sample = check_articles(today_start, today_start + timedelta(days=1))
print(f"[오늘 수집 기사] 총 {today_count}건")
for t, c in today_sample:
    print(f"  - ({c}) {t}")

# =========================
# 2. 어제 수집 기사 확인
# =========================
yesterday_count, yesterday_sample = check_articles(yesterday_start, yesterday_end)
print(f"\n[어제 수집 기사] 총 {yesterday_count}건")
for t, c in yesterday_sample:
    print(f"  - ({c}) {t}")

# =========================
# 3. 로그 최근 10줄
# =========================
if os.path.exists(LOG_FILE):
    print(f"\n[최근 로그 10줄] ({LOG_FILE})")
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.strip())
else:
    print(f"\n로그 파일이 존재하지 않습니다: {LOG_FILE}")

# =========================
# 4. 테스트 메일 발송
# =========================
TEST_BODY = f"뉴스 크롤러 시스템 테스트\n오늘 기사 수: {today_count}\n어제 기사 수: {yesterday_count}\n"
TEST_SUBJECT = f"[news_crawler TEST] {datetime.now().date()} 수집 확인"

proc = subprocess.Popen(
    ["mail", "-s", TEST_SUBJECT, "vjihyun.bangv@gmail.com"],
    stdin=subprocess.PIPE,
    text=True
)
proc.communicate(TEST_BODY)
print("\n테스트 메일 발송 완료 ✅")

cur.close()
conn.close()

