import firebase_admin
from firebase_admin import credentials, messaging

# =========================================
# ✅ Firebase 초기화 (앱이 중복 초기화되지 않도록 처리)
# =========================================
def initialize_firebase():
    """
    Firebase Admin SDK 초기화 (한 번만 실행)
    """
    if not firebase_admin._apps:
        cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json")
        firebase_admin.initialize_app(cred)
        print("🔥 Firebase 초기화 완료")
    else:
        print("✅ Firebase 이미 초기화됨")


# =========================================
# ✅ FCM 푸시 전송 함수
# =========================================
def send_fcm_notification(fcm_token: str, title: str, body: str) -> bool:
    """
    지정된 FCM 토큰으로 알림을 전송하는 함수

    Args:
        fcm_token (str): 대상 사용자의 FCM 토큰
        title (str): 알림 제목
        body (str): 알림 본문

    Returns:
        bool: 전송 성공 여부
    """
    try:
        initialize_firebase()

        # 메시지 생성
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=title,
                body=body,
            )
        )

        # 메시지 전송
        response = messaging.send(message)
        print(f"✅ 메시지 전송 성공: {response}")
        return True

    except Exception as e:
        print(f"❌ 메시지 전송 실패: {e}")
        return False


# =========================================
# ✅ 테스트 실행 (직접 실행 시)
# =========================================
if __name__ == "__main__":
    token = "c-Btjy_7oEtBvw8f_sQ0mv:APA91bELRshMqNU32Rme8L5QYRXcIwQ13RP6Ov0cWURMRz_Tql9rjgXpWEgnNcg1whvwhxpOstkH_tHwpHrkax5T5-YwznSHUnS_XNKpVZp-sBYSDjDk7Fg"
    title = "새 팝업 오픈 🎉"
    body = "짱구 팝업이 부산에서 열렸어요!\n11.05 ~ 11.15"

    token = "c-Btjy_7oEtBvw8f_sQ0mv:APA91bELRshMqNU32Rme8L5QYRXcIwQ13RP6Ov0cWURMRz_Tql9rjgXpWEgnNcg1whvwhxpOstkH_tHwpHrkax5T5-YwznSHUnS_XNKpVZp-sBYSDjDk7Fg"
    title = "[짱구] 소식 도착!"
    body = "짱구 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    token = "c-Btjy_7oEtBvw8f_sQ0mv:APA91bELRshMqNU32Rme8L5QYRXcIwQ13RP6Ov0cWURMRz_Tql9rjgXpWEgnNcg1whvwhxpOstkH_tHwpHrkax5T5-YwznSHUnS_XNKpVZp-sBYSDjDk7Fg"
    title = "[쿵야] 소식 도착!"
    body = "쿵야 야채스타 팝업이 서울에서 열렸어요!\n📅 11.10 ~ 11.12"

    # 준태
    # token = "fn0x0b82RDWJJVc3lrkLyA:APA91bEluBCuiqupWibrnTbdTVOIDHepsBgRTXM4hwZi88BTdZgAyzo2ikfb7vNP-FLTBjPzEfaI3U-IiHUSu1rJrdve7cK7Nk22rGQgDA1PmPd3NImJbJc"
    # title = "신기한 소식 도착!"
    # body = "이준태 죽으"

    # 카카오 동현
    token = "c0wS67HPQkO5uDjUVQxfqm:APA91bF_1MiilVc53141G7FT8ahq5Y2zWPITNEAkCmCkvIXuUYgtCkZZZh6xedNKY21ufqlPMw5jP069bAHzix7eZknXeQyVqJI80bH-KSpXM8c46pLXi1Y"
    title = "[쿵야] 소식 도착!"
    body = "쿵야 야채스타 팝업이 서울에서 열렸어요!\n📅 11.10 ~ 11.12"

    token = "c0wS67HPQkO5uDjUVQxfqm:APA91bF_1MiilVc53141G7FT8ahq5Y2zWPITNEAkCmCkvIXuUYgtCkZZZh6xedNKY21ufqlPMw5jP069bAHzix7eZknXeQyVqJI80bH-KSpXM8c46pLXi1Y"
    title = "[짱구] 소식 도착!"
    body = "짱구 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    token = "c0wS67HPQkO5uDjUVQxfqm:APA91bF_1MiilVc53141G7FT8ahq5Y2zWPITNEAkCmCkvIXuUYgtCkZZZh6xedNKY21ufqlPMw5jP069bAHzix7eZknXeQyVqJI80bH-KSpXM8c46pLXi1Y"
    title = "[화장품] 소식 도착!"
    body = "센텀 화장품 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    # token = "c0wS67HPQkO5uDjUVQxfqm:APA91bF_1MiilVc53141G7FT8ahq5Y2zWPITNEAkCmCkvIXuUYgtCkZZZh6xedNKY21ufqlPMw5jP069bAHzix7eZknXeQyVqJI80bH-KSpXM8c46pLXi1Y"
    # title = "[빼빼로] 소식 도착!"
    # body = "빼빼로데이 스틱 팝업이 서울에서 열렸어요!\n📅 11.07 ~ 11.13"

    token = "cShLK9Mi90PCu9L-rGt0c0:APA91bH00HxTAWzZ3nXQzhfNDDg-sFIkORQrS3lXS40EQbzOP_PDO29vHhey3gZ13E3Z2UGj9qvSn-sHsftPSPULxwM1tfp0t37t38aSolFRcImAe4_poUo"
    title = "[짱구] 소식 도착!"
    body = "짱구 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    token = "dDZss77PqUZGrqfK5tCSYC:APA91bGOsh8wVxfnhKdzbrMshyOHZeA8n5CHmunEMHJFGnlAkK6Dk6auFtt4YB2tzgDcDTDIXsqbMpK4qQyQpl08Yb2fxA-xo8AomN-OaBYg-bs2-R5LN-w"
    title = "[화장품] 소식 도착!"
    body = "센텀 화장품 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"




    token = "dDZss77PqUZGrqfK5tCSYC:APA91bGOsh8wVxfnhKdzbrMshyOHZeA8n5CHmunEMHJFGnlAkK6Dk6auFtt4YB2tzgDcDTDIXsqbMpK4qQyQpl08Yb2fxA-xo8AomN-OaBYg-bs2-R5LN-w"
    title = "[팝업] 소식 도착!"
    body = "센텀 화장품 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    token = "dDZss77PqUZGrqfK5tCSYC:APA91bGOsh8wVxfnhKdzbrMshyOHZeA8n5CHmunEMHJFGnlAkK6Dk6auFtt4YB2tzgDcDTDIXsqbMpK4qQyQpl08Yb2fxA-xo8AomN-OaBYg-bs2-R5LN-w"
    title = "[화장품, 팝업, 팝업스토어, 디올] 소식 도착!"
    body = "센텀 화장품 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    token = "dDZss77PqUZGrqfK5tCSYC:APA91bGOsh8wVxfnhKdzbrMshyOHZeA8n5CHmunEMHJFGnlAkK6Dk6auFtt4YB2tzgDcDTDIXsqbMpK4qQyQpl08Yb2fxA-xo8AomN-OaBYg-bs2-R5LN-w"
    title = "[화장품, 팝업스토어, 디올] 소식 도착!"
    body = "센텀 화장품 팝업이 부산에서 열렸어요!\n📅 11.05 ~ 11.15"

    
    send_fcm_notification(token, title, body)
