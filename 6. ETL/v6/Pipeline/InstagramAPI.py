import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional

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


# DTO 정의
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
        self.log = Logger("InstagramAPI", use_color=False)

    # 주어진 해시태그 텍스트로부터 Instagram Graph API의 해시태그 ID를 조회
    def get_hashtag_id(self, hashtag: str) -> Optional[str]:
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
        
    # 특정 해시태그 ID에 대한 최근 게시물들을 조회 → DTO 변환
    def get_recent_media(self, hashtag_id: str, limit: int = 5) -> List[InstagramPostDTO]:
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
    
    # DTO 리스트를 Json 파일로 저장
    def save_json(self, data: List[InstagramPostDTO], filename: str):
        # dataclass -> dict 변환
        json_data = [post.__dict__ for post in data]

        # json 파일로 저장
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            self.log.info(f"데이터가 '{filename}'에 저장되었습니다.")
        except IOError as e:
            self.log.error(f"❌ 파일 저장 실패: {e}")

    @staticmethod
    def play():

        # .env 로드
        load_dotenv()
        BASE_URL = "https://graph.facebook.com/v20.0"
        ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
        USER_ID = os.getenv("IG_USER_ID")
        hashtag = "팝업스토어"

        # 인스턴스 생성
        log = Logger("InstaAPI")
        api = InstagramAPI(ACCESS_TOKEN, USER_ID, BASE_URL)

        # .env 값이 없으면 종료
        if not ACCESS_TOKEN or not USER_ID:
            log.error("❌ .env 설정 누락: ACCESS_TOKEN 또는 IG_USER_ID")
            return

        # 해시태그 ID 조회 => 17842967191006184 반환
        hashtag_id = api.get_hashtag_id(hashtag)
        if not hashtag_id:
            log.error(f"❌ 해시태그 ID를 찾을 수 없습니다: {hashtag}")
            return
        
        posts = api.get_recent_media(hashtag_id, limit=3)
        api.save_json(posts, "popup.json")
        
        
if __name__ == "__main__":
    InstagramAPI.play()