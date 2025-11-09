import requests
import os
from dotenv import load_dotenv

# .env 예시:
# INSTA_ACCESS_TOKEN=현재_비즈니스용_토큰
# FB_APP_ID=페이스북_앱_ID
# FB_APP_SECRET=페이스북_앱_SECRET

load_dotenv()
ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")

def refresh_facebook_graph_token():
    if not all([ACCESS_TOKEN, APP_ID, APP_SECRET]):
        print("❌ 환경변수 누락: FB_APP_ID, FB_APP_SECRET, INSTA_ACCESS_TOKEN 확인 필요")
        return

    url = "https://graph.facebook.com/v20.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": ACCESS_TOKEN
    }

    response = requests.get(url, params=params).json()
    if "access_token" in response:
        new_token = response["access_token"]
        expires_in = response.get("expires_in", 0)
        print("✅ 새 토큰 발급 완료")
        print(f"만료까지 약 {expires_in / 86400:.1f}일 ({expires_in}초)")

        # ✅ .env 갱신
        lines = []
        with open(".env", "r") as f:
            lines = f.readlines()

        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("INSTA_ACCESS_TOKEN="):
                    f.write(f"INSTA_ACCESS_TOKEN={new_token}\n")
                else:
                    f.write(line)

        print("📝 .env 갱신 완료")
    else:
        print("❌ 갱신 실패:", response)

if __name__ == "__main__":
    refresh_facebook_graph_token()
