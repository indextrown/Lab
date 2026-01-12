import requests, os
from dotenv import load_dotenv

# .env 예시:
# FB_APP_ID=페이스북_앱_ID
# FB_APP_SECRET=페이스북_앱_SECRET
# INSTA_ACCESS_TOKEN=EAA단기토큰

load_dotenv()
APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
SHORT_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")

def exchange_for_long_lived_token():
    url = "https://graph.facebook.com/v20.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": SHORT_TOKEN
    }

    response = requests.get(url, params=params).json()
    if "access_token" in response:
        new_token = response["access_token"]
        expires_in = response.get("expires_in", 0)
        print("✅ 60일짜리 장기 토큰 발급 완료")
        print(f"Access Token: {new_token[:60]}...")
        print(f"만료까지 약 {expires_in / 86400:.1f}일 ({expires_in}초)")

        # .env 업데이트
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
        print("❌ 교환 실패:", response)

if __name__ == "__main__":
    exchange_for_long_lived_token()
