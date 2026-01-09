"""프로그램 실행 진입점, 각 모듈 연계. DB 연결, 테이블 구조, CRUD"""
# src/db.py
import mysql.connector
from mysql.connector import Error

def get_connection():
    """MariaDB 연결 후 connection 반환"""
    try:
        conn = mysql.connector.connect(
            host='192.168.1.24',      # MariaDB 서버 주소
            user='ktech',         # DB 사용자
            password='ktech!@#$',     # DB 비밀번호
            database='boannews'     # 사용할 DB
        )
        return conn
    except Error as e:
        print("DB 연결 실패:", e)
        return None

def save_article(conn, article: dict):
    """RSS에서 읽은 기사 DB에 저장 (중복 링크 처리)"""
    cursor = conn.cursor()
    sql = """
    INSERT INTO articles (title, link, published, summary, source, category, author)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        title=VALUES(title),
        published=VALUES(published),
        summary=VALUES(summary),
        category=VALUES(category),
        author=VALUES(author)
    """
    cursor.execute(sql, (
        article['title'],
        article['link'],
        article.get('published'),
        article.get('summary'),
        article.get('source', 'boannews'),
        article.get('category'),
        article.get('author')
    ))
    conn.commit()