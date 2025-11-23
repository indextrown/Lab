import os
import json
import pymysql
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, messaging

# -------------------------------------------------
# Logger import: main 실행 + 단독 실행 모두 지원
# -------------------------------------------------
try:
    # 패키지 실행(main.py) 시: Pipeline → 상위 폴더 → Logger.py
    from .Logger import Logger
except ImportError:
    # 단독 실행(Pipeline/InstagramAPI.py) 시: sys.path로 상위 폴더 추가
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Logger import Logger

# ==============================================
# 🔥 Firebase Service
# ==============================================
class FirebaseService:
    _initialized = False

    @staticmethod
    def init():
        if not FirebaseService._initialized:
            cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json")
            firebase_admin.initialize_app(cred)
            FirebaseService._initialized = True

    @staticmethod
    def send(token: str, title: str, body: str) -> bool:
        if not token:
            return False

        try:
            FirebaseService.init()
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(title=title, body=body),
            )
            messaging.send(message)
            return True
        except Exception as e:
            print(f"❌ FCM 실패: {e}")
            return False
        
# ==============================================
# 🗄 MySQL Connection
# ==============================================
class MySQL:
    @staticmethod
    def connect(local=True):
        load_dotenv()
        host = "127.0.0.1" if local else "poppang.co.kr"

        return pymysql.connect(
            host=host,
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
    
# ==============================================
# Popup Repository (mysql.json 로더)
# ==============================================
class PopupRepository:

    @staticmethod
    def load_popups():
        """
        mysql.json에 저장된 팝업 데이터 로드
        """
        path = os.path.join(os.getcwd(), "mysql.json")

        if not os.path.exists(path):
            print("❌ mysql.json 없음")
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
# ==============================================
# User + Keyword Repository(알림 받을 대상 유저 + 그 유저의 키워드들 가져오기)
# ==============================================
class UserRepository:

    @staticmethod
    def get_users_with_keywords(conn):
        """
        [
            {
                "user_id": 1,
                "nickname": "동현",
                "fcm_token": "...",
                "keywords": ["팝업", "전시", "카페"]
            }
        ]
        """
        sql = """
        SELECT 
            u.id AS user_id,
            u.nickname,
            u.fcm_token,
            k.alert_keyword AS keyword
        FROM users u
        JOIN user_alert_keyword k ON u.id = k.users_id
        WHERE u.is_deleted = 0
          AND u.is_alerted = 1
        """

        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        users = {}
        for row in rows:
            uid = row["user_id"]
            if uid not in users:
                users[uid] = {
                    "user_id": uid,
                    "nickname": row["nickname"],
                    "fcm_token": row["fcm_token"],
                    "keywords": []
                }
            users[uid]["keywords"].append(row["keyword"])

        return list(users.values())
    
# ==============================================
# UserAlert 기록 Repository
# ==============================================
class UserAlertRepository:

    @staticmethod
    def insert(conn, user_id, popup_id):
        sql = """
        INSERT INTO user_alert (users_id, popup_id)
        SELECT %s, %s
        FROM DUAL
        WHERE NOT EXISTS (
            SELECT 1 FROM user_alert
            WHERE users_id = %s AND popup_id = %s
        )
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, popup_id, user_id, popup_id))
            conn.commit()
        except Exception as e:
            print(f"❌ user_alert INSERT 실패: {e}")

# ==============================================
# UserAlert 기록 Repository
# ==============================================
class UserAlertRepository:

    @staticmethod
    def insert(conn, user_id, popup_id):
        sql = """
        INSERT INTO user_alert (users_id, popup_id)
        SELECT %s, %s
        FROM DUAL
        WHERE NOT EXISTS (
            SELECT 1 FROM user_alert
            WHERE users_id = %s AND popup_id = %s
        )
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, popup_id, user_id, popup_id))
            conn.commit()
        except Exception as e:
            print(f"❌ user_alert INSERT 실패: {e}")

# ==============================================
# Alert 파이프라인
# ==============================================
class Alert:
    log = Logger("AlertAPI", use_color=False) 

    @staticmethod
    def play(local=False):

        # DB 연결
        conn = MySQL.connect(local)

        try:
            # 1) 유저 + 키워드 로드
            users = UserRepository.get_users_with_keywords(conn)

            # 2) 팝업 로드 (mysql.json)
            popups = PopupRepository.load_popups()
            if not popups: return

            # 3) 유저별 처리
            total_alert_users = 0
            for user in users:
                uid = user["user_id"]
                nickname = user["nickname"]
                token = user["fcm_token"]
                keywords = user["keywords"]

                matched = []
                matched_kw = set()

                for popup in popups:
                    title = popup.get("name", "")
                    summary = popup.get("caption_summary", "")

                    for kw in keywords:
                        if kw in title or kw in summary:
                            matched.append(popup)
                            matched_kw.add(kw)
                
                if matched:
                    total_alert_users += 1

                    print(f"\n🔔 알림 대상: {nickname} / 키워드: {keywords}")

                    # DB 기록 추가
                    for popup in matched:
                        pid = popup.get("popup_id")
                        if pid:
                            UserAlertRepository.insert(conn, uid, pid)

                    # 알림 1회 발송
                    first = matched[0]
                    hashtag = " ".join([f"#{k}" for k in matched_kw])
                    title = "[팝팡] 새로운 팝업 소식!"
                    body = f"{first['name']} {first.get('region','')}에서 열렸어요!\n\n{hashtag}"
                    FirebaseService.send(token, title, body)
                else:
                    print(f"🔍 {nickname} — 매칭 없음")
            Alert.log.info(f"✅ 완료 — 총 알림 유저 {total_alert_users}")
        finally:
            conn.close()

if __name__ == "__main__":
    Alert.play(local=False)
