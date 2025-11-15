import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from FCM import send_fcm_notification

# .env 파일 로드
load_dotenv()

def fetch_all_fcm_tokens():
    try:
        # DB 연결
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),       # ← 여기 추가됨
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

        cursor = conn.cursor(dictionary=True)

        # FCM 전체 조회
        # cursor.execute("SELECT uuid, fcm_token FROM users")
        # isAlerted = 1인 유저만 조회 (중요!)
        cursor.execute("""
            SELECT uuid, fcm_token 
            FROM users
            WHERE is_alerted = 1
        """)
        rows = cursor.fetchall()

        print("전체 사용자에게 알림을 보냅니다.")
        for row in rows:
            print(f"{row['uuid']} → {row['fcm_token']}")
            send_fcm_notification(
                fcm_token=row['fcm_token'],
                title="공지사항 🔔",
                body="팝팡 알림 반복 테스트 예정입니다. 알림을 해제해주세요."
            )

        return rows

    except Error as e:
        print("❌ MySQL Error:", e)

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# 실행
fetch_all_fcm_tokens()
