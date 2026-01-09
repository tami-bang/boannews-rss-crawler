# test_db.py
import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host='192.168.1.24',
        user='ktech',
        password='ktech!@#$',
        database='boannews'
    )
    if conn.is_connected():
        print("DB 연결 성공!")
    conn.close()
except Error as e:
    print("DB 연결 실패:", e)
