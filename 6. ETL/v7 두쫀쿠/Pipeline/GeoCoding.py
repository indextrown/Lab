import requests
import urllib.parse
import os
import json
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional, List
# -------------------------------------------------
# Logger import: main 실행 + 단독 실행 모두 지원
# -------------------------------------------------
try:
    from .Logger import Logger
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Logger import Logger


# ==============================
# DTO 정의
# ==============================
@dataclass
class PlaceInfoDTO:
    road_address: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]

# ==============================
# GeoCoding 클래스
# ==============================
class GeoCoding:
    """
    GPT 결과 JSON에 Naver 지오코딩 정보를 추가하는 파이프라인 단계.
    - 입력: gpt.json
    - 출력: geo.json
    """
    log = Logger("GeoCodingAPI", use_color=False) 

    # 환경변수 로드 + 필수 키 체크
    @staticmethod
    def load_keys():
        load_dotenv()
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("❌ CLIENT_ID / CLIENT_SECRET 환경 변수가 누락되었습니다.")

        return client_id, client_secret

    # Naver API 요청
    @classmethod
    def get_place_info(cls, query: str) -> PlaceInfoDTO:
        """장소명 검색 → 주소 + 좌표 반환"""

        client_id, client_secret = cls.load_keys()

        encoded = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/local.json?query={encoded}&display=1"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if 'items' in data and data['items']:
                item = data['items'][0]
                road_addr = item.get('roadAddress') or item.get('address')

                try:
                    lng = float(item['mapx']) / 10_000_000 if item.get('mapx') else None
                    lat = float(item['mapy']) / 10_000_000 if item.get('mapy') else None
                except Exception:
                    lng, lat = None, None

                road_addr = cls.normalize_address(road_addr)

                return PlaceInfoDTO(
                    road_address=road_addr,
                    longitude=lng,
                    latitude=lat
                )

        except Exception as e:
            cls.log.warn(f"⚠️ API 실패({query}): {e}")

        return PlaceInfoDTO(None, None, None)
    
    # 주소 변환
    @classmethod
    def normalize_address(cls, address: Optional[str]) -> Optional[str]:
        if not address:
            return address

        replacements = {
            "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
            "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
            "울산광역시": "울산", "경기도": "경기", "충청북도": "충북",
            "충청남도": "충남", "전라북도": "전북", "전라남도": "전남",
            "경상북도": "경북", "경상남도": "경남", "세종특별자치시": "세종",
            "전북특별자치도": "전북", "제주특별자치도": "제주",
            "강원특별자치도": "강원"
        }

        original = address

        # 1) 도/시 앞부분 치환
        for old, new in replacements.items():
            if old in address:
                address = address.replace(old, new)

        # 2) "서울시" → "서울" 처리
        parts = address.split(" ", 1)
        if parts and parts[0].endswith("시"):
            parts[0] = parts[0].removesuffix("시")

        address = " ".join(parts)

        if original == address:
            cls.log.warn(f"⚠️ 치환 없음: {original}")

        return address
    
    # 파일 읽기
    @staticmethod
    def file_open(filename: str):
        if not os.path.exists(filename):
            GeoCoding.log.error(f"❌ 파일 없음: {filename}")
            return []

        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
        
    # 파일 저장
    @staticmethod
    def file_save(data: List[dict], filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        abs_path = os.path.abspath(filename)
        GeoCoding.log.info(f"📁 저장 완료: {abs_path}")
        return abs_path
    
    # gpt.json → geo.json 생성
    @classmethod
    def enrich_geocoding(cls, input_file="gpt.json", output_file="geo.json"):
        data = cls.file_open(input_file)
        if not data:
            return

        enriched = []
        skipped = 0

        for item in data:
            query = item.get("geocoding_query") or item.get("address")

            if not query:
                cls.log.warn(f"⚠️ 지오코딩 대상 없음: {item.get('name')}")
                skipped += 1
                continue

            info = cls.get_place_info(query)

            if info.longitude is None or info.latitude is None:
                cls.log.warn(f"🚫 위경도 없음 → 스킵: {item.get('name')} ({query})")
                skipped += 1
                continue

            # 정상 데이터 추가
            enriched.append({
                **item,
                "road_address": info.road_address,
                "longitude": info.longitude,
                "latitude": info.latitude,
            })

        cls.file_save(enriched, output_file)

    # 파이프라인 실행
    @staticmethod
    def play():
        GeoCoding.enrich_geocoding()\
        
if __name__ == "__main__":
    GeoCoding.play()