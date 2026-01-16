# ============================================================
# send_daily_summary_test.py
# 목적: CRON 전 안전 테스트용
# - 오늘/어제 기사 조회
# - HTML 태그 제거
# - 기사 수 표시
# - 실제 메일 발송 없이 본문 출력
# ============================================================

import pymysql
from datetime import datetime, timedelta
import re

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
# 2. RSS URL → 카테고리 이름 매핑
# =========================
CATEGORY_MAP = {
    "http://www.boannews.com/media/news_rss.xml?mkind=1": "SECURITY",
    "http://www.boannews.com/media/news_rss.xml?mkind=2": "IT",
    "http://www.boannews.com/media/news_rss.xml?mkind=4": "SAFETY",
    "http://www.boannews.com/media/news_rss.xml?mkind=5": "SecurityWorld",
    "http://www.boannews.com/media/news_rss.xml?kind=1": "사건ㆍ사고",
    "http://www.boannews.com/media/news_rss.xml?kind=2": "공공ㆍ정책",
    "http://www.boannews.com/media/news_rss.xml?kind=3": "비즈니스",
    "http://www.boannews.com/media/news_rss.xml?kind=4": "국제",
    "http://www.boannews.com/media/news_rss.xml?kind=5": "테크",
    "http://www.boannews.com/media/news_rss.xml?kind=6": "오피니언",
    "http://www.boannews.com/media/news_rss.xml?skind=5": "긴급경보",
    "http://www.boannews.com/media/news_rss.xml?skind=7": "기획특집",
    "http://www.boannews.com/media/news_rss.xml?skind=3": "인터뷰",
    "http://www.boannews.com/media/news_rss.xml?skind=2": "보안컬럼",
    "http://www.boannews.com/media/news_rss.xml?skind=6": "보안정책",
}

CATEGORY_ORDER = ["전체기사"] + list(CATEGORY_MAP.values())

# =========================
# 3. 시간 범위 (어제)
# =========================
today = datetime.now().date()
start_dt = datetime.combine(today - timedelta(days=1), datetime.min.time())
end_dt = datetime.combine(today, datetime.min.time())

# =========================
# 4. DB 연결 및 조회
# =========================
conn = pymysql.connect(**DB)
cur = conn.cursor()

# 전체기사 조회
cur.execute("""
    SELECT title, summary
    FROM articles
    WHERE fetched_at >= %s AND fetched_at < %s
    ORDER BY fetched_at ASC
""", (start_dt, end_dt))
articles_by_category = {"전체기사": cur.fetchall()}

# 카테고리별 조회
for url, cat_name in CATEGORY_MAP.items():
    cur.execute("""
        SELECT title, summary
        FROM articles
        WHERE fetched_at >= %s AND fetched_at < %s AND category = %s
        ORDER BY fetched_at ASC
    """, (start_dt, end_dt, url))

    rows = cur.fetchall()
    existing_titles = {t for (t, _) in articles_by_category["전체기사"]}
    filtered = [(t, s) for (t, s) in rows if t not in existing_titles]
    articles_by_category[cat_name] = filtered

cur.close()
conn.close()

# =========================
# 5. HTML 제거 + None 처리
# =========================
def clean_text(text):
    if not text:
        return "내용 없음"
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# =========================
# 6. 본문 구성 및 출력
# =========================
total_articles = sum(len(v) for v in articles_by_category.values())
if total_articles == 0:
    body = f"{start_dt.date()} 수집 기사 없음\n"
else:
    body = f"{start_dt.date()} 수집 기사 요약 (총 {total_articles}건)\n\n"
    for cat in CATEGORY_ORDER:
        news_list = articles_by_category.get(cat, [])
        if not news_list:
            continue

        body += f" {cat} \n"
        for i, (title, summary) in enumerate(news_list, 1):
            body += f"{i}. {clean_text(title)}\n"
            body += f"   - {clean_text(summary)}\n"
        body += "\n"

print(body)
print(f"총 기사 수: {total_articles}")
if total_articles == 0:
    print("※ 어제 수집된 기사가 없습니다.")

