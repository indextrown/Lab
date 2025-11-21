import os
import json
import pymysql
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, messaging
from Logger import Logger


# ==============================================
# 🔥 Firebase 모듈
# ==============================================
def initialize_firebase():
    """ Firebase Admin SDK 초기화 (중복 방지) """
    if not firebase_admin._apps:
        cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json")
        firebase_admin.initialize_app(cred)


def send_fcm_notification(fcm_token: str, title: str, body: str) -> bool:
    """ FCM 전송 """
    if not fcm_token:
        print("⚠️  FCM 토큰 없음 → 스킵")
        return False

    try:
        initialize_firebase()
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(title=title, body=body),
        )
        response = messaging.send(message)
        print(f"✅ FCM 전송 성공 → {response}")
        return True
    except Exception as e:
        print(f"❌ FCM 전송 실패: {e}")
        return False


# ==============================================
# 🗄 DB Utility
# ==============================================
def get_connection(local=True):
    """ MySQL 연결 """
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
# 📌 쿼리 함수 — 유저별 키워드 묶어서 반환
# ==============================================
def fetch_user_keywords_grouped(conn):
    """
    결과 형태:
    [
        {
            "user_id": 1,
            "nickname": "김동현",
            "fcm_token": "...",
            "keywords": ["팝업", "짱구"]
        }
    ]
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.id AS user_id,
                u.nickname,
                u.fcm_token,
                k.alert_keyword AS keyword
            FROM users u
            JOIN user_alert_keyword k ON u.id = k.users_id
            WHERE u.is_deleted = 0
              AND u.is_alerted = 1
        """)
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
# 📌 user_alert INSERT (중복 방지)
# ==============================================
def insert_user_alert(conn, user_id, popup_id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_alert (users_id, popup_id)
                SELECT %s, %s
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM user_alert
                    WHERE users_id = %s AND popup_id = %s
                )
            """, (user_id, popup_id, user_id, popup_id))

        conn.commit()
        print(f"💾 user_alert INSERT → user={user_id}, popup={popup_id}")
    except Exception as e:
        print(f"❌ user_alert INSERT 실패: {e}")


# ==============================================
# 📚 mysql.json 로드
# ==============================================
def load_popup_json():
    json_path = os.path.join(os.getcwd(), "mysql.json")
    if not os.path.exists(json_path):
        print("❌ mysql.json 없음")
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================
# 🎯 Alert 메인
# ==============================================
class Alert:
    log = Logger("AlertAPI")

    @staticmethod
    def play(local=False):

        # 1) DB 연결
        conn = get_connection(local)

        try:
            # 2) 유저별 키워드 가져오기 (그룹 형태)
            users = fetch_user_keywords_grouped(conn)

            # 3) mysql.json 로드
            popups = load_popup_json()
            if not popups:
                return

            total_alert_users = 0

            # 4) 유저별 처리
            for user in users:
                user_id = user["user_id"]
                nickname = user["nickname"]
                fcm_token = user["fcm_token"]
                keywords = user["keywords"]

                matched_popups = []
                matched_keywords = set()

                for popup in popups:
                    title = popup.get("name", "")
                    summary = popup.get("caption_summary", "")

                    for kw in keywords:
                        if kw in title or kw in summary:
                            matched_popups.append(popup)
                            matched_keywords.add(kw)

                # ⚡ 매칭되면 알림 처리
                if matched_popups:
                    total_alert_users += 1

                    print("\n==============================")
                    print(f"📨 알림 대상: {nickname} (user_id={user_id})")
                    print(f"🔑 키워드: {keywords}")
                    print(f"🎯 매칭된 팝업 수: {len(matched_popups)}")
                    print("==============================")

                    # DB 기록 (팝업별 user_alert)
                    for popup in matched_popups:
                        popup_id = popup.get("popup_id")
                        if popup_id:
                            insert_user_alert(conn, user_id, popup_id)

                    # 알림은 1회만
                    hashtag = " ".join([f"#{kw}" for kw in matched_keywords])
                    first_popup = matched_popups[0]

                    notif_title = f"[팝팡] 새로운 팝업 소식!"
                    notif_body = (
                        f"{first_popup['name']} "
                        f"{first_popup.get('region','')}에서 열렸어요!\n\n"
                        f"{hashtag}"
                    )

                    send_fcm_notification(fcm_token, "최종 테스트입니다" + notif_title, notif_body)

                else:
                    Alert.log.plain(f"🔍 [{nickname}] 매칭된 팝업 없음")

            Alert.log.plain(f"✅ Alert 종료 — 총 알림 대상 유저: {total_alert_users}")

        except Exception as e:
            Alert.log.error(f"❌ Alert 실행 오류: {e}")

        finally:
            conn.close()
            Alert.log.info("🔌 DB 연결 종료\n\n\n")



# ==============================================
# 실행
# ==============================================
if __name__ == "__main__":
    Alert.play(local=False)
