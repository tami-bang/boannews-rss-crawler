import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import send_daily_summary as sds

from fastapi import FastAPI
from src.db import get_connection

app = FastAPI(title="BoanNews RSS API", description="BoanNews RSS 크롤러 API", version="1.0")

@app.get("/articles")
def list_articles(limit: int = 100):
    """
    최신 뉴스 조회
    - limit: 반환할 뉴스 건수 (기본 100)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles ORDER BY published DESC LIMIT %s", (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"articles": result}

@app.get("/send-summary")
def send_summary():
    """
    일간 요약 메일 발송 트리거
    """
    sds.send_daily_summary()  # 기존 함수 호출
    return {"status": "메일 발송 완료"}

