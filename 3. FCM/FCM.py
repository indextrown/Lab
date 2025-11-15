"""
Firebase FCM 클라이언트 모듈

다른 코드에서 import하여 바로 사용 가능:
from fcm.firebase_client import send_fcm_notification
"""

import firebase_admin
from firebase_admin import credentials, messaging
import os
from functools import lru_cache


# =====================================================
# 🔥 Firebase 초기화 (한 번만 실행되도록 캐싱)
# =====================================================
@lru_cache(maxsize=1)
def initialize_firebase():
    """
    Firebase Admin SDK를 한 번만 초기화한다.
    lru_cache 로직 덕분에 중복 초기화 방지.
    """
    if not firebase_admin._apps:
        cred_path = os.path.join(
            os.path.dirname(__file__),
            "poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json"  # 서비스 키 파일명에 맞게 변경
        )

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        print("🔥 Firebase 초기화 완료")
    else:
        print("⚡ Firebase 이미 초기화됨")

    return True


# =====================================================
# 📌 FCM 푸시 전송 함수 (재사용용)
# =====================================================
def send_fcm_notification(fcm_token: str, title: str, body: str) -> bool:
    """
    지정된 FCM 토큰으로 알림을 전송하는 함수.

    Args:
        fcm_token (str): FCM Device Token
        title (str): 알림 제목
        body (str): 알림 본문
    Returns:
        bool: 성공 True / 실패 False
    """

    try:
        initialize_firebase()

        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
        )

        response = messaging.send(message)
        print(f"✅ 메시지 전송 성공: {response}")
        return True

    except Exception as e:
        print(f"❌ 메시지 전송 실패: {e}")
        return False
