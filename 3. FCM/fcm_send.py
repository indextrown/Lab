import firebase_admin
from firebase_admin import credentials, messaging

# 1. 서비스 계정 키 경로 (.json)
cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-84728d5589.json")
firebase_admin.initialize_app(cred)

# 2. 대상 유저의 FCM 토큰
# fcm_token = "c-PxUkfo4U3Fpaegcg3AU0:APA91bGBC513AfSGA8qTge0GY45iKOs8MVJc5c3IHwEYB_QE_yLv3vQvJUjN4Q7Z8yvO0iM4JWMwnWslZfD8LT3WEsUklK841AhWXXForqu3uWVEXtwy5Uc" # 도날드
fcm_token = "c-Btjy_7oEtBvw8f_sQ0mv:APA91bELRshMqNU32Rme8L5QYRXcIwQ13RP6Ov0cWURMRz_Tql9rjgXpWEgnNcg1whvwhxpOstkH_tHwpHrkax5T5-YwznSHUnS_XNKpVZp-sBYSDjDk7Fg"


# 내용
title = "새 팝업 오픈 🎉"
body = "짱구 팝업이 부산에서 열렸어요!\n11.05 ~ 11.09"

# 4. 알림 메시지 구성
message = messaging.Message(
    token=fcm_token,
    notification=messaging.Notification(
        title=title,
        body=body,
    )
)

# 5. 메시지 전송
try:
    response = messaging.send(message)
    print("✅ 메시지 전송 성공:", response)
except Exception as e:
    print("❌ 메시지 전송 실패:", e)




# import firebase_admin
# from firebase_admin import credentials, messaging

# cred = credentials.Certificate("./poppangfcm-firebase-adminsdk-fbsvc-a66201d92b.json")
# firebase_admin.initialize_app(cred)

# fcm_token = "feCfGbFEYEnahc6jz95idz:APA91bEUm294z_-XG3xtKBdNsHdX7H5C-vFzStKRs7IAjLXN_76KAG18cfQZ8tXI7zAE6Qllt1xCSTLhAOQd1vkfZQjRmeCtfU4KzPVIIqkXgNfzzU4tUok"

# message = messaging.Message(
#     token=fcm_token,
#     notification=messaging.Notification(
#         title="팝팡 테스트 알림",
#         body="새로운 팝업이 열렸어요!"
#     ),
#     apns=messaging.APNSConfig(
#         headers={
#             "apns-priority": "10",
#             "apns-push-type": "alert"  # iOS 13+ 필수
#         },
#         payload=messaging.APNSPayload(
#             aps=messaging.Aps(
#                 alert=messaging.ApsAlert(
#                     title="팝팡 테스트 알림",
#                     body="새로운 팝업이 열렸어요!"
#                 ),
#                 sound="default",
#                 badge=1
#             )
#         )
#     )
# )

# try:
#     response = messaging.send(message)
#     print("✅ 메시지 전송 성공:", response)
# except Exception as e:
#     print("❌ 메시지 전송 실패:", e)
