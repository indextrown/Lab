# mysql> desc users;
# +------------+--------------------------------+------+-----+---------+-------------------+
# | Field      | Type                           | Null | Key | Default | Extra             |
# +------------+--------------------------------+------+-----+---------+-------------------+
# | id         | bigint                         | NO   | PRI | NULL    | auto_increment    |
# | uid        | varchar(255)                   | NO   | UNI | NULL    |                   |
# | uuid       | varchar(36)                    | YES  |     | uuid()  | DEFAULT_GENERATED |
# | provider   | enum('APPLE','GOOGLE','KAKAO') | YES  |     | NULL    |                   |
# | email      | varchar(255)                   | YES  |     | NULL    |                   |
# | nickname   | varchar(255)                   | YES  | UNI | NULL    |                   |
# | role       | enum('ADMIN','MEMBER')         | YES  |     | NULL    |                   |
# | is_alerted | tinyint(1)                     | NO   |     | 0       |                   |
# | fcm_token  | varchar(255)                   | YES  |     | NULL    |                   |
# | is_deleted | tinyint(1)                     | NO   |     | 0       |                   |
# | created_at | datetime                       | YES  |     | NULL    |                   |
# | updated_at | datetime                       | YES  |     | NULL    |                   |
# +------------+--------------------------------+------+-----+---------+-------------------+
# 12 rows in set (0.01 sec)

# mysql> desc user_alert_keyword;
# users_id => user의 id를의미
# +---------------+--------------+------+-----+---------+----------------+
# | Field         | Type         | Null | Key | Default | Extra          |
# +---------------+--------------+------+-----+---------+----------------+
# | id            | bigint       | NO   | PRI | NULL    | auto_increment |
# | users_id      | bigint       | NO   | MUL | NULL    |                |
# | alert_keyword | varchar(100) | NO   | UNI | NULL    |                |
# +---------------+--------------+------+-----+---------+----------------+
# 3 rows in set (0.00 sec)

# 이 코드에서 join으로 두 테이블 합친다 users + user_alert_keyword = user_keywords
# 유저별 키워드 + fcm_token 조회
# 기준
# u.id = users.id
# k.users_id = user_alert_keyword.user_id
# +--------------+-----------+
# | Field        | Type      |
# +--------------+-----------+
# | user_id      | int        |
# | nickname     | varchar    |
# | fcm_token    | varchar    |
# | keyword      | varchar    |
# +--------------+-----------+


import os
import json
import pymysql
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, messaging
from Logger import Logger


# ==============================================
# ✅ Firebase 초기화 함수
# ==============================================
def initialize_firebase():
    """Firebase Admin SDK 초기화 (중복 방지)"""
    if not firebase_admin._apps:
        cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json")
        firebase_admin.initialize_app(cred)
        # print("🔥 Firebase 초기화 완료")
    # 이미 초기화된 경우는 그냥 패스


# ==============================================
# ✅ FCM 발송 함수
# ==============================================
def send_fcm_notification(fcm_token: str, title: str, body: str) -> bool:
    """
    지정된 FCM 토큰으로 알림 전송

    Args:
        fcm_token (str): 사용자 FCM 토큰
        title (str): 알림 제목
        body (str): 알림 내용

    Returns:
        bool: 성공 여부
    """
    if not fcm_token:
        print("⚠️ FCM 토큰 없음 → 전송 스킵")
        return False

    try:
        initialize_firebase()
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=title,
                body=body,
            )
        )
        response = messaging.send(message)
        Alert.log.plain(f"FCM 전송 성공 → {response}")
        return True
    except Exception as e:
        print(f"❌ FCM 전송 실패: {e}")
        return False


# ==============================================
# ✅ Alert 클래스
# ==============================================
class Alert:
    log = Logger("AlertAPI")

    @staticmethod
    def play(local: bool = True):
        """
        1️⃣ user_alert_keyword 테이블에서 유저별 키워드 + fcm_token 조회
        2️⃣ mysql.json 불러오기
        3️⃣ 각 유저 키워드와 popup의 name / caption_summary 비교
        4️⃣ 일치 시 콘솔 출력 + FCM 알림 전송
        """
        load_dotenv()

        # ✅ DB 분기
        if local:
            DB_HOST = "127.0.0.1"
            # Alert.log.plain("🌱 로컬 DB 활성화")
        else:
            DB_HOST = "poppang.co.kr"   # 실제 배포용 DB 호스트로 맞춰두면 됨
            # Alert.log.plain("🚀 배포 DB 활성화")

        connection = None

        try:
            # ✅ MySQL 연결
            connection = pymysql.connect(
                host=DB_HOST,
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )

            with connection.cursor() as cursor:
                # ✅ 유저별 키워드 + fcm_token 조회
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
                user_keywords = cursor.fetchall()

            # ✅ mysql.json 로드
            json_path = os.path.join(os.getcwd(), "mysql.json")
            if not os.path.exists(json_path):
                Alert.log.error("❌ mysql.json 파일이 없습니다.")
                return

            with open(json_path, "r", encoding="utf-8") as f:
                popups = json.load(f)

            total_alert_users = 0

            # ✅ 매칭 로직 (이제 matches 제대로 사용)
            for user in user_keywords:
                nickname = user["nickname"]
                keyword = user["keyword"]
                fcm_token = user.get("fcm_token")

                matches = []
                for popup in popups:
                    title = popup.get("name", "")
                    caption_summary = popup.get("caption_summary", "")

                    if keyword in title or keyword in caption_summary:
                        matches.append(popup)

                if matches:
                    total_alert_users += 1
                    Alert.log.plain(f"📢 [{nickname}]님의 키워드 '{keyword}' 관련 팝업 발견!")
                    Alert.log.plain(f"   🔔 FCM 토큰: {fcm_token}")

                    # 콘솔용 리스트 출력
                    for popup in matches:
                        preview = popup.get("caption_summary", "")[:70].replace("\n", " ")
                        Alert.log.plain(f"   🎪 {popup['name']} | 내용: {preview}...")

                    # 🔔 FCM 전송 (팝업마다 한 번씩)
                    for popup in matches:
                        title = popup.get("name", "")
                        region = popup.get("region", "")
                        start = popup.get("start_date", "")
                        end = popup.get("end_date", "")

                        notif_title = f"[{keyword}] 소식 도착!"
                        notif_body = f"{title}이 {region}에서 열렸어요!"
                        # notif_body = f"{title}이 {region}에서 열렸어요!\n📅 {start} ~ {end}"

                        send_fcm_notification(fcm_token, notif_title, notif_body)
                else:
                    Alert.log.plain(f"🔍 [{nickname}] 키워드 '{keyword}' 관련 팝업 없음")
            Alert.log.plain(f"✅ Alert 완료 (알림 대상 유저 수: {total_alert_users})")
        except Exception as e:
            Alert.log.error(f"❌ Alert 실행 중 오류: {e}")
        finally:
            if connection is not None:
                connection.close()
                Alert.log.info("🔌 DB 커넥션 종료\n\n\n")
                print()


if __name__ == "__main__":
    Alert.play(local=False)
