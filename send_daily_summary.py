# ============================================================
# send_daily_summary.py
# 목적: 운영용 일일 뉴스 헤드라인 메일 발송
# - 집계 범위: 어제 06:00 ~ 오늘 06:00
# - 발송 시각: 매일 06:00 (cron)
# - 제목 자체에 링크 포함 (HTML 메일)
# - cron 로그에 실행 시간 표시
# ============================================================

import pymysql
import subprocess
from datetime import datetime, timedelta
import re

# ============================================================
# 1. 메인 함수 정의
# ============================================================
def send_daily_summary():
    """
    FastAPI 또는 스크립트에서 호출 가능한 일간 뉴스 요약 메일 발송 함수.
    """
    # ============================================================
    # 1-1. 로그 출력 함수
    # ============================================================
    def log(msg):
        """현재 시간과 메시지를 함께 출력"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] {msg}")

    # ============================================================
    # 1-2. DB 접속 정보 (MariaDB)
    # ============================================================
    DB = {
        "host": "localhost",            # DB 서버 주소
        "user": "newsbot",              # DB 사용자
        "password": "newsbot_pass!",    # DB 비밀번호
        "database": "boannews",         # 사용할 DB 이름
        "charset": "utf8mb4"
    }

    # ============================================================
    # 2. RSS URL → 카테고리 이름 매핑
    # ============================================================
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

    # 전체 기사 먼저 보여주고, 그 뒤 카테고리별 순서대로
    CATEGORY_ORDER = ["전체기사"] + list(CATEGORY_MAP.values())

    # ============================================================
    # 3. 집계 시간 범위 (고정)
    # ============================================================
    today = datetime.now().date()
    start_dt = datetime.combine(today - timedelta(days=1), datetime.min.time()) + timedelta(hours=6)
    end_dt   = datetime.combine(today, datetime.min.time()) + timedelta(hours=6)
    log(f"집계 범위: {start_dt} ~ {end_dt}")

    # ============================================================
    # 4. DB 연결
    # ============================================================
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    # ============================================================
    # 5. 전체기사 조회
    # ============================================================
    cur.execute("""
        SELECT title, link
        FROM articles
        WHERE fetched_at >= %s AND fetched_at < %s
        ORDER BY fetched_at ASC
        LIMIT 5
    """, (start_dt, end_dt))

    articles_by_category = {"전체기사": cur.fetchall()}

    # ============================================================
    # 6. 카테고리별 조회
    # ============================================================
    for url, cat_name in CATEGORY_MAP.items():
        cur.execute("""
            SELECT title, link
            FROM articles
            WHERE fetched_at >= %s
              AND fetched_at < %s
              AND category = %s
            ORDER BY fetched_at ASC
            LIMIT 3
        """, (start_dt, end_dt, url))

        rows = cur.fetchall()
        # 전체기사에 이미 있는 제목은 중복 제거
        existing_titles = {t for (t, _) in articles_by_category["전체기사"]}
        articles_by_category[cat_name] = [
            (t, l) for (t, l) in rows if t not in existing_titles
        ]

    cur.close()
    conn.close()

    # ============================================================
    # 7. HTML 정제 함수
    # ============================================================
    def clean_text(text):
        """HTML 태그 제거 및 공백 정리"""
        if not text:
            return ""
        text = re.sub(r"<[^>]*>", "", text)
        return re.sub(r"\s+", " ", text).strip()

    # ============================================================
    # 8. HTML 메일 본문 구성
    # ============================================================
    total_articles = sum(len(v) for v in articles_by_category.values())

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
    <h2>{start_dt.date()} 뉴스 헤드라인</h2>
    <p>※ 어제 06:00 ~ 오늘 06:00 수집 기사 기준</p>
    """

    if total_articles == 0:
        body += "<p><b>수집된 기사가 없습니다.</b></p>"
    else:
        for cat in CATEGORY_ORDER:
            news_list = articles_by_category.get(cat, [])
            if not news_list:
                continue

            body += f"<h3>[{cat}]</h3><ol>"
            for title, link in news_list:
                body += f'<li><a href="{link}">{clean_text(title)}</a></li>'
            body += "</ol>"

    body += "</body></html>"

    # ============================================================
    # 9. 메일 발송 (HTML)
    # ============================================================
    subject = f"[news_crawler] {start_dt.date()} 뉴스 헤드라인"
    to_addr = "vjihyun.bangv@gmail.com"
    from_addr = "newsbot@localhost"

    mail_body = f"""From: {from_addr}
To: {to_addr}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

{body}
"""

    proc = subprocess.Popen(
        ["/usr/sbin/sendmail", "-t"],
        stdin=subprocess.PIPE,
        text=True
    )
    proc.communicate(mail_body)

    log(f"메일 발송 완료 (총 {total_articles}건)")
    if total_articles == 0:
        log("수집된 기사가 없습니다.")


# ============================================================
# 스크립트 실행용
# ============================================================
if __name__ == "__main__":
    send_daily_summary()

