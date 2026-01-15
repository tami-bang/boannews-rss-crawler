# test_send_mail.py
"""
오늘 수집된 기사 확인 + 메일 발송 테스트
- DB에서 오늘 기사 조회
- 제목 + summary 포함
- 메일 발송
"""

import pymysql
from datetime import datetime
import subprocess

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
# 오늘 시간 범위
# =========================
today_start = datetime.combine(datetime.now().date(), datetime.min.time())

# =========================
# DB 조회
# =========================
conn = pymysql.connect(**DB)
cur = conn.cursor()

cur.execute("""
    SELECT title, summary
    FROM articles
    WHERE fetched_at >= %s
    ORDER BY fetched_at ASC
    LIMIT 10
""", (today_start,))

rows = cur.fetchall()
cur.close()
conn.close()

if not rows:
    print("오늘 수집된 기사가 없습니다 ❌")
else:
    print(f"오늘 수집 기사 수: {len(rows)} ✅")

# =========================
# 메일 본문 구성
# =========================
body = f"{datetime.now().date()} 오늘 수집 기사 요약\n\n"

for i, (title, summary) in enumerate(rows, 1):
    body += f"{i}. {title}\n"
    if summary:
        body += f"   - {summary}\n"
body += "\n"

subject = f"[news_crawler TEST] {datetime.now().date()} 기사 요약"

# =========================
# 메일 발송
# =========================
proc = subprocess.Popen(
    ["mail", "-s", subject, "vjihyun.bangv@gmail.com"],  # 수신자
    stdin=subprocess.PIPE,
    text=True
)
proc.communicate(body)

print("메일 발송 완료 ✅")

