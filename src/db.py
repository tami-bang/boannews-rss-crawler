"""프로그램 실행 진입점, 각 모듈 연계. DB 연결, 테이블 구조, CRUD"""
# src/db.py
import mysql.connector
from mysql.connector import Error

def get_connection():
    """MariaDB 연결 후 connection 반환"""
    try:
        conn = mysql.connector.connect(
            host='192.168.1.24',      # MariaDB 서버 주소
            #host='잘못된 주소',          # DB 연결 실패 테스트
            user='ktech',              # DB 사용자
            password='ktech!@#$',      # DB 비밀번호
            database='boannews'        # 사용할 DB
        )
        return conn
    except Error as e:
        print("DB 연결 실패:", e)
        return None

def save_article(conn, article):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT IGNORE INTO articles
            (title, link, published, summary, source, category, author)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            article['title'],
            article['link'],
            article['published'],
            article['summary'],
            article['source'],
            article['category'],
            article['author']
        ))
        conn.commit()  # 이 줄이 반드시 필요
    except Exception as e:
        conn.rollback()
        logging.error(f"DB 저장 실패: {e}")
    finally:
        cursor.close()

def archive_old_articles(conn, days: int = 1):
    """articles → articles_old 이관 후 articles 정리"""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO articles_old
        SELECT * FROM articles
        WHERE fetched_at < NOW() - INTERVAL %s DAY
    """, (days,))

    cursor.execute("""
        DELETE FROM articles
        WHERE fetched_at < NOW() - INTERVAL %s DAY
    """, (days,))

    conn.commit()
