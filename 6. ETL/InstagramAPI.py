import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
from Logger import Logger

# ✅ .env 로드
load_dotenv()
BASE_URL = os.getenv("API_BASE_URL")

# ✅ DTO 정의
@dataclass
class InstagramPostDTO:
    id: str
    caption: Optional[str]
    media_type: str
    permalink: str
    timestamp: str
    media_urls: List[str]

class InstagramAPI:
    def __init__(self, access_token: str, user_id: str, base_url: str):
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = base_url
        self.log = Logger("InstaAPI") 

    def get_hashtag_id(self, hashtag: str) -> Optional[str]:
        """
        주어진 해시태그 텍스트로부터 Instagram Graph API의 해시태그 ID를 조회
        """
        url = f"{self.base_url}/ig_hashtag_search"
        params = {
            "user_id": self.user_id,
            "q": hashtag,
            "access_token": self.access_token
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])

            if not data:
                self.log.warn(f"⚠️ 해시태그 ID를 찾을 수 없습니다: '{hashtag}'")
                return None
            return data[0]["id"]
        except requests.RequestException as e:
            self.log.error(f"❌ 해시태그 ID 요청 실패: {e}")
            return None

    def get_recent_media(self, hashtag_id: str, limit: int = 5) -> List[InstagramPostDTO]:
        """
        특정 해시태그 ID에 대한 최근 게시물들을 조회 → DTO 변환
        """
        url = f"{self.base_url}/{hashtag_id}/recent_media"
        params = {
            "user_id": self.user_id,
            "access_token": self.access_token,
            "fields": (
                "id,caption,media_type,media_url,permalink,comments_count,"
                "like_count,timestamp,children{media_url,media_type}"
            ),
            "limit": limit
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            json_data = response.json()
            raw_posts = json_data.get("data", [])

            parsed_posts: List[InstagramPostDTO] = []
            for item in raw_posts:
                if item["media_type"] not in ("IMAGE", "CAROUSEL_ALBUM"):
                    continue

                media_urls: List[str] = []

                if item["media_type"] == "CAROUSEL_ALBUM" and "children" in item:
                    for child in item["children"]["data"]:
                        if "media_url" in child:
                            media_urls.append(child["media_url"])
                elif "media_url" in item:
                    media_urls.append(item["media_url"])

                post_dto = InstagramPostDTO(
                    id=item.get("id"),
                    caption=item.get("caption"),
                    media_type=item.get("media_type"),
                    permalink=item.get("permalink"),
                    timestamp=item.get("timestamp"),
                    media_urls=media_urls
                )
                parsed_posts.append(post_dto)

            return parsed_posts

        except requests.RequestException as e:
            self.log.error(f"❌ 요청 실패: {e}")
        except ValueError:
            self.log.error("❌ JSON 파싱 실패")
        return []

    def save_json(self, data: List[InstagramPostDTO], filename_prefix="media", hashtag=None):
        """
        DTO 리스트를 JSON 파일로 저장
        """
        # hashtag_part = f"_{hashtag}" if hashtag else ""
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"{filename_prefix}{hashtag_part}_{timestamp}.json"
        filename = "popup.json"  # ✅ 파일 이름 고정

        # dataclass → dict 변환
        json_data = [post.__dict__ for post in data]

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            self.log.info(f"저장 완료: {os.path.abspath(filename)}")
        except Exception as e:
            self.log.error(f"❌ 저장 실패: {e}")

    @staticmethod
    def play():
        """
        실행 진입점
        """
        load_dotenv()
        access_token = os.getenv("INSTA_ACCESS_TOKEN")
        user_id = os.getenv("IG_USER_ID")
        hashtag = "팝업스토어"
        base_url = "https://graph.facebook.com/v20.0"
        log = Logger("InstaAPI")

        if not access_token or not user_id:
            log.error("❌ .env 설정 누락: ACCESS_TOKEN 또는 IG_USER_ID")
            return

        api = InstagramAPI(access_token, user_id, base_url)
        hashtag_id = api.get_hashtag_id(hashtag)
        if not hashtag_id:
            log.error(f"❌ 해시태그 ID를 찾을 수 없습니다: {hashtag}")
            return

        posts = api.get_recent_media(hashtag_id)
        api.save_json(posts, hashtag=hashtag)

if __name__ == "__main__":
    InstagramAPI.play()
