# src/api.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import send_daily_summary as sds

from fastapi import FastAPI
from src.db import get_connection
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(
    title="BoanNews RSS API",
    description="BoanNews RSS 크롤러 API - 뉴스 조회 및 일간 요약 메일 발송",
    version="1.0"
)

# ============================================================
# 1. Pydantic 모델 정의 (Swagger용)
# ============================================================
class Article(BaseModel):
    id: int = Field(..., description="기사 ID", example=1)
    title: str = Field(..., description="기사 제목", example="보안 취약점 발견")
    link: str = Field(..., description="기사 링크 URL", example="http://www.boannews.com/article/1234")
    category: str = Field(..., description="기사 카테고리", example="SECURITY")
    published: str = Field(..., description="발행 시각 (문자열)", example="2026-01-15 08:05:00")

class ArticlesResponse(BaseModel):
    articles: List[Article] = Field(
        ...,
        description="기사 목록",
        example={
            "articles": [
                {
                    "id": 1,
                    "title": "보안 취약점 발견",
                    "link": "http://www.boannews.com/article/1234",
                    "category": "SECURITY",
                    "published": "2026-01-15 08:05:00"
                },
                {
                    "id": 2,
                    "title": "IT 정책 변화",
                    "link": "http://www.boannews.com/article/1235",
                    "category": "IT",
                    "published": "2026-01-15 07:55:00"
                }
            ]
        }
    )

# ============================================================
# 2. 뉴스 조회 API
# ============================================================
@app.get(
    "/articles",
    response_model=ArticlesResponse,
    summary="최신 뉴스 조회",
    description="DB에 저장된 최신 뉴스 리스트를 반환합니다. limit는 최대 반환 건수입니다.",
    responses={
        200: {"description": "성공"},
        500: {"description": "DB 연결 실패 또는 기타 서버 오류"}
    },
    tags=["뉴스 조회"]
)
def list_articles(limit: int = 100):
    """
    최신 뉴스 조회
    - limit: 반환할 뉴스 건수 (기본 100)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles ORDER BY published DESC LIMIT %s", (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # datetime → str 변환 (Swagger/JSON 호환)
    for row in rows:
        row["published"] = row["published"].strftime("%Y-%m-%d %H:%M:%S")

    return {"articles": rows}

# ============================================================
# 3. 일간 요약 메일 발송 API
# ============================================================
@app.get(
    "/send-summary",
    summary="일간 요약 메일 발송",
    description="DB에서 어제~오늘 수집한 뉴스 헤드라인을 메일로 발송합니다.",
    responses={
        200: {"description": "메일 발송 성공", "content": {"application/json": {"example": {"status": "메일 발송 완료"}}}},
        500: {"description": "메일 발송 실패"}
    },
    tags=["메일 발송"]
)
def send_summary():
    """
    일간 요약 메일 발송 트리거
    """
    sds.send_daily_summary()  # 기존 함수 호출
    return {"status": "메일 발송 완료"}

