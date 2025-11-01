# GeoCoding.py
import requests
import urllib.parse
import os
import json
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional, List


# ==============================
# 📦 DTO 정의
# ==============================

@dataclass
class PlaceInfoDTO:
    road_address: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]


# ==============================
# 🧭 GeoCoding 로직
# ==============================

class GeoCoding:
    """
    GPT 결과 JSON에 도로명주소 및 좌표(경도/위도)를 추가하는 클래스.
    - Naver Local Search API를 사용 (장소명 기반)
    - 결과를 popup_with_geo.json으로 저장
    """

    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("❌ CLIENT_ID / CLIENT_SECRET 환경 변수가 누락되었습니다.")

    # -----------------------------------
    # 📍 1. 장소 검색 (Naver Local API)
    # -----------------------------------
    def get_place_info(self, query: str) -> PlaceInfoDTO:
        """장소명으로 검색 후 주소와 좌표 반환"""
        encoded_query = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/local.json?query={encoded_query}&display=1"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if 'items' in data and data['items']:
                item = data['items'][0]
                road_address = item.get('roadAddress') or item.get('address')

                # 좌표값이 비어있는 경우도 대비
                try:
                    longitude = float(item['mapx']) / 10_000_000 if item.get('mapx') else None
                    latitude = float(item['mapy']) / 10_000_000 if item.get('mapy') else None
                except Exception:
                    longitude, latitude = None, None

                road_address = self.normalize_address(road_address)

                return PlaceInfoDTO(
                    road_address=road_address,
                    longitude=longitude,
                    latitude=latitude
                )

        except Exception as e:
            print(f"⚠️ Geocoding 실패 ({query}): {e}")

        return PlaceInfoDTO(
            road_address=None,
            longitude=None,
            latitude=None
        )

    # -----------------------------------
    # 🪄 주소 변환 로직
    # -----------------------------------
    def normalize_address(self, address: Optional[str]) -> Optional[str]:
        if not address:
            return address

        replacements = {
            # 공식 17개
            "서울특별시": "서울",
            "부산광역시": "부산",
            "대구광역시": "대구",
            "인천광역시": "인천",
            "광주광역시": "광주",
            "대전광역시": "대전",
            "울산광역시": "울산",
            "경기도": "경기",
            "충청북도": "충북",
            "충청남도": "충남",
            "전라북도": "전북",
            "전라남도": "전남",
            "경상북도": "경북",
            "경상남도": "경남",
            "세종특별자치시": "세종",
            "전북특별자치도": "전북",
            "제주특별자치도": "제주",
            "강원특별자치도": "강원",
        }

        original = address
        for old, new in replacements.items():
            if old in address:
                address = address.replace(old, new)

        parts = address.split(" ", 1)
        if parts and parts[0].endswith("시"):
            parts[0] = parts[0].removesuffix("시")
        address = " ".join(parts)

        if address == original:
            print(f"⚠️ 치환 대상 아님: {original}")

        return address

    # -----------------------------------
    # 🗺 2. popup_refined.json → 좌표추가
    # -----------------------------------
    def add_geocoding_to_json(
        self,
        input_file: str = "gpt.json",
        output_file: str = "geo.json"
    ):
        """
        입력 JSON에 road_address / longitude / latitude 추가 후 저장
        geocoding_query 필드를 우선 사용하고, 없으면 address 사용
        위경도 값이 없을 경우 필터링
        """
        if not os.path.exists(input_file):
            print(f"❌ 입력 파일 없음: {input_file}")
            return

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        enriched = []
        skipped = 0
        for event in data:
            query = event.get("geocoding_query") or event.get("address")
            if not query:
                print(f"⚠️ 지오코딩 대상 없음: {event.get('name')}")
                skipped += 1
                continue

            place_info = self.get_place_info(query)

            # 📌 위경도 값 없는 경우 제외
            if place_info.longitude is None or place_info.latitude is None:
                print(f"🚫 위경도 없음 → 스킵: {event.get('name')} ({query})")
                skipped += 1
                continue

            # ✅ 정상 데이터만 추가
            new_event = {**event}
            new_event["road_address"] = place_info.road_address
            new_event["longitude"] = place_info.longitude
            new_event["latitude"] = place_info.latitude

            enriched.append(new_event)

        # 3️⃣ 저장
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

        print(f"✅ Geocoding 완료: {output_file} (총 {len(enriched)}건, 스킵 {skipped}건)")

    # -----------------------------------
    # 🚀 3. 실행 메서드
    # -----------------------------------
    @staticmethod
    def play():
        geo = GeoCoding()
        geo.add_geocoding_to_json()
        print()


if __name__ == "__main__":
    GeoCoding.play()