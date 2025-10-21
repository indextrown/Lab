import os
import json
import requests
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# ✅ Vision 기능 import
import VisionAPI


# ==============================
# 📦 DTO 정의
# ==============================

@dataclass
class PopupImageDTO:
    imageUrl: str
    sortOrder: int

@dataclass
class PopupUploadDTO:
    name: str
    startDate: str
    endDate: str
    openTime: Optional[str]
    closeTime: Optional[str]
    address: str
    roadAddress: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    region: str
    geocodingQuery: str
    instaPostId: str
    instaPostUrl: str
    captionSummary: str
    caption: str
    mediaType: str
    imageList: List[PopupImageDTO]
    recommendIdList: List[int]
    isActive: bool = True


# ==============================
# 🧭 유틸 함수
# ==============================

def convert_to_public_path(local_path: str) -> str:
    """절대 경로를 /images/... 상대 경로로 변환"""
    if "/images/" in local_path:
        idx = local_path.index("/images/")
        return local_path[idx:]
    return local_path


def build_image_list(image_paths: List[str]) -> List[PopupImageDTO]:
    """image_paths → DTO 리스트 변환"""
    return [
        PopupImageDTO(
            imageUrl=convert_to_public_path(path),
            sortOrder=idx
        )
        for idx, path in enumerate(image_paths)
    ]


def build_payload(item: dict) -> PopupUploadDTO:
    """원본 dict → DTO 변환"""
    image_paths = item.get("image_paths", [])
    image_list = build_image_list(image_paths)

    return PopupUploadDTO(
        name=item.get("name"),
        startDate=item.get("start_date"),
        endDate=item.get("end_date"),
        openTime=item.get("open_time"),
        closeTime=item.get("close_time"),
        address=item.get("address"),
        roadAddress=item.get("road_address"),
        longitude=item.get("longitude"),
        latitude=item.get("latitude"),
        region=item.get("region"),
        geocodingQuery=item.get("geocoding_query"),
        instaPostId=item.get("insta_post_id"),
        instaPostUrl=item.get("insta_post_url"),
        captionSummary=item.get("caption_summary"),
        caption=item.get("caption"),
        mediaType=item.get("media_type"),
        imageList=image_list,
        recommendIdList=item.get("recommend"),
    )


# ==============================
# 🐬 Mysql 업로드 클래스
# ==============================

class Mysql:
    @staticmethod
    def send_popup(item: dict, api_url: str) -> bool:
        """Vision 통과한 팝업 정보를 API로 업로드"""
        payload_dto = build_payload(item)
        payload = json.loads(json.dumps(payload_dto, default=lambda o: o.__dict__))

        print("\n📤 업로드 요청 payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        headers = {"Content-Type": "application/json"}
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"✅ 업로드 성공: {payload_dto.instaPostId}")
            return True
        else:
            print(f"❌ 업로드 실패 ({response.status_code}): {payload_dto.instaPostId}")
            print(response.text)
            return False

    @staticmethod
    def play():
        # ✅ 환경 변수 로드 (GeoCoding 방식과 동일)
        env_path = os.path.join(os.getcwd(), ".env")
        file_path = os.path.join(os.getcwd(), "geo.json")
        load_dotenv(dotenv_path=env_path, override=True)

        API_URL = os.getenv("POPUP_API_URL", "https://poppang.co.kr/api/v1/popup")

        print(f"📂 Working DIR: {os.getcwd()}")
        print(f"📄 JSON 경로: {file_path} → 존재? {os.path.exists(file_path)}")
        print(f"🌐 API URL: {API_URL}")

        if not os.path.exists(file_path):
            print("❌ geo.json 파일이 없습니다.")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        total = len(data)
        inserted = 0
        skipped = 0
        human_skipped = 0

        for item in data:
            insta_post_id = item.get("insta_post_id")
            media_type = item.get("media_type")
            image_paths = item.get("image_paths", [])

            print(f"\n📌 처리중: insta_post_id={insta_post_id}")
            print(f"📸 이미지 경로: {image_paths}")

            # 🎥 VIDEO Vision 스킵
            if media_type == "VIDEO":
                print(f"🎥 VIDEO 타입 → Vision 검사 스킵")
                if Mysql.send_popup(item, API_URL):
                    inserted += 1
                else:
                    skipped += 1
                continue

            # 🧠 Vision 검사 (IMAGE, CAROUSEL_ALBUM)
            if image_paths:
                try:
                    has_human = VisionAPI.contains_human_in_all_files(image_paths)
                    if has_human:
                        human_skipped += 1
                        print(f"🚫 Vision 감지됨 → 업로드 스킵 insta_post_id={insta_post_id}")
                        continue
                except Exception as e:
                    print(f"❌ Vision 검사 중 오류: {e}")
                    skipped += 1
                    continue
            else:
                print(f"⚠️ image_paths 비어있음 → Vision 검사 스킵")

            # ✅ Vision 통과 후 업로드
            if Mysql.send_popup(item, API_URL):
                inserted += 1
            else:
                skipped += 1

        print("\n===============================")
        print(f"✅ 업로드 완료: {inserted}/{total}")
        print(f"🚫 Vision 필터로 스킵: {human_skipped}")
        print(f"⚠️ 오류 또는 기타 스킵: {skipped}")
        print("===============================")


# ==============================
# 🏁 실행
# ==============================
if __name__ == "__main__":
    Mysql.play()
