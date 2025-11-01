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

class Alert:
    @staticmethod
    def play():
        """
        1️⃣ user_alert_keyword 테이블에서 유저별 키워드 + fcm_token 조회
        2️⃣ mysql.json 불러오기
        3️⃣ 각 유저 키워드와 popup의 name / caption_summary 비교
        4️⃣ 일치 시 print()로 알림 출력 (+ FCM 토큰도 함께)
        """
        load_dotenv()

        try:
            # ✅ MySQL 연결
            connection = pymysql.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )

            with connection.cursor() as cursor:
                # ✅ 유저별 키워드 + fcm_token 조회
                # users와 user_alert_keyword 테이블을 합친다
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

                cursor.execute("""
                SELECT 
                    u.id AS user_id,
                    u.nickname,
                    u.fcm_token,
                    k.alert_keyword AS keyword
                FROM users u
                JOIN user_alert_keyword k ON u.id = k.users_id
                WHERE u.is_deleted = 0
                """)
                user_keywords = cursor.fetchall()

            # ✅ JSON 데이터 로드
            json_path = os.path.join(os.getcwd(), "mysql.json")
            if not os.path.exists(json_path):
                print("❌ mysql.json 파일이 없습니다.")
                return

            with open(json_path, "r", encoding="utf-8") as f:
                popups = json.load(f)

            # ✅ 매칭 로직
            for user in user_keywords:
                nickname = user["nickname"]
                keyword = user["keyword"]
                fcm_token = user.get("fcm_token", None)

                matches = []
                for popup in popups:
                    title = popup.get("name", "")
                    caption_summary = popup.get("caption_summary", "")

                    if keyword in title or keyword in caption_summary:
                        matches.append(popup)

                if matches:
                    print(f"\n📢 [{nickname}]님의 키워드 '{keyword}' 관련 팝업 발견!")
                    print(f"   🔔 FCM 토큰: {fcm_token}")
                    for popup in matches:
                        preview = popup["caption_summary"][:70].replace("\n", " ")
                        print(f"   🎪 {popup['name']} | 내용: {preview}...")
                else:
                    print(f"🔍 [{nickname}] 키워드 '{keyword}' 관련 팝업 없음")

        except Exception as e:
            print(f"❌ Alert 실행 중 오류: {e}")
        finally:
            connection.close()
            print("\n✅ Alert 완료")

if __name__ == "__main__":
    Alert.play()
