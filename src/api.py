# ============================================================
# src/api.py
# FastAPI 서버 - BoanNews RSS API
# - 뉴스 조회: /articles
# - 일간 요약 메일 발송: /send-summary
# - CORS 허용, pub_date alias 적용, RSS URL → DB 키 매핑
# ============================================================

import sys
import os
from typing import List
from datetime import datetime

# 상위 경로 import 허용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.db import get_connection
import send_daily_summary as sds

# ============================
# FastAPI 앱 생성
# ============================
app = FastAPI(
    title="BoanNews RSS API",
    description="BoanNews RSS 크롤러 API - 뉴스 조회 및 일간 요약 메일 발송",
    version="1.0"
)

# ============================
# CORS 설정 (Next.js에서 fetch 가능)
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 배포 시 실제 프론트 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Pydantic 모델 정의
# ============================
class Article(BaseModel):
    id: int = Field(..., description="기사 ID")
    title: str = Field(..., description="기사 제목")
    link: str = Field(..., description="뉴스 URL")
    category: str = Field(..., description="뉴스 카테고리 (DB 키 기준)")
    pub_date: str = Field(..., description="발행 시각 (ISO8601 문자열)")

class ArticlesResponse(BaseModel):
    articles: List[Article] = Field(..., description="뉴스 리스트")

# ============================
# RSS URL → DB 키 매핑
# ============================
CATEGORY_MAPPING = {
    # 메인 카테고리
    "http://www.boannews.com/media/news_rss.xml?mkind=1": "security",
    "http://www.boannews.com/media/news_rss.xml?mkind=2": "it",
    "http://www.boannews.com/media/news_rss.xml?mkind=4": "safety",
    "http://www.boannews.com/media/news_rss.xml?mkind=5": "securityworld",
    # 뉴스 카테고리
    "http://www.boannews.com/media/news_rss.xml": "all",
    "http://www.boannews.com/media/news_rss.xml?kind=1": "incidents",
    "http://www.boannews.com/media/news_rss.xml?kind=2": "public-policy",
    "http://www.boannews.com/media/news_rss.xml?kind=3": "business",
    "http://www.boannews.com/media/news_rss.xml?kind=4": "international",
    "http://www.boannews.com/media/news_rss.xml?kind=5": "tech",
    "http://www.boannews.com/media/news_rss.xml?kind=6": "opinion",
    # 세부 카테고리
    "http://www.boannews.com/media/news_rss.xml?skind=5": "emergency",
    "http://www.boannews.com/media/news_rss.xml?skind=7": "feature",
    "http://www.boannews.com/media/news_rss.xml?skind=3": "interview",
    "http://www.boannews.com/media/news_rss.xml?skind=2": "column",
    "http://www.boannews.com/media/news_rss.xml?skind=6": "policy",
}

# ============================
# 1. 뉴스 조회 API
# ============================
@app.get("/articles", response_model=ArticlesResponse, summary="최신 뉴스 조회", tags=["뉴스 조회"])
def list_articles(limit: int = 100):
    """
    최신 뉴스 조회 API
    - limit: 반환할 뉴스 건수 (기본 100)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, title, link, category, fetched_at FROM articles "
            "ORDER BY fetched_at DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()

    except Exception as e:
        raise RuntimeError(f"DB 조회 실패: {e}")
    finally:
        cursor.close()
        conn.close()

    # ============================
    # datetime → ISO8601, RSS URL → DB 키 매핑 적용
    # ============================
    for row in rows:
        row["pub_date"] = row.pop("fetched_at").strftime("%Y-%m-%dT%H:%M:%SZ")
        # URL → DB 키 변환
        row["category"] = CATEGORY_MAPPING.get(row["category"], row["category"])

    return {"articles": rows}

# ============================
# 2. 일간 뉴스 요약 메일 발송 API
# ============================
@app.get("/send-summary", summary="일간 뉴스 요약 메일 발송", tags=["메일 발송"])
def send_summary():
    """
    /send-summary 호출 시 send_daily_summary.py 함수를 실행하여
    어제~오늘 수집 뉴스 헤드라인을 HTML 메일로 발송
    """
    try:
        sds.send_daily_summary()
    except Exception as e:
        raise RuntimeError(f"메일 발송 실패: {e}")

    return {"status": "메일 발송 완료"}

