import os
import json
import pymysql
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


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

# -------------------------------------------------
# VisionAPI import 
# -------------------------------------------------
try:
    from .VisionAPI import contains_human_in_all_files
except ImportError:
    from VisionAPI import contains_human_in_all_files

# ==============================
# Util
# ==============================
# 절대경로(/Users/...) → /images/... 로 변환
def to_server_path(local_path: str) -> str:
    if "/images/" in local_path:
        return local_path[local_path.index("/images/"):]
    return local_path

# ==============================
# DTO 정의
# ==============================
@dataclass
class PopupImageDTO:
    imageUrl: str
    sortOrder: int

    @staticmethod
    def to_dto(image_paths: List[str]) ->List["PopupImageDTO"]:
        return [
            PopupImageDTO(
                imageUrl=path,
                sortOrder=index
            )
            for index, path in enumerate(image_paths)
        ]

@dataclass
class PopupDTO:
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

    @staticmethod
    def to_dto(item: dict) -> "PopupDTO":
        image_paths = item.get("image_paths", [])
        return PopupDTO(
            name = item.get("name"),
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
            imageList=PopupImageDTO.to_dto(image_paths),
            recommendIdList=item.get("recommend", []),
        )

# ==============================
# Mysql 업로드 클래스
# ==============================
class Mysql:
    log = Logger("Mysql", use_color=False) 

    # 파일 읽기
    @staticmethod
    def file_open(filename: str):
        if not os.path.exists(filename):
            Mysql.log.error(f"❌ 파일 없음: {filename}")
            return []
        
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    # 파일 저장
    @staticmethod
    def file_save(results, filename="mysql.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        Mysql.log.info(f"📁 저장 완료 → {os.path.abspath(filename)}")

    # DB 연결
    @staticmethod
    def connect_db(local=True):
        load_dotenv()
        host = "127.0.0.1" if local else os.getenv("DB_HOST")

        return pymysql.connect(
            host=host,
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    # Vision 검사 + 영상 제외
    @staticmethod
    def validate(dto: PopupDTO) -> bool:

        # VIDEO 제외
        if dto.mediaType == "VIDEO":
            Mysql.log.warn(f"🚫 영상 스킵: {dto.name}")
            return False

        # VisionAPI 얼굴 포함 여부 검사
        try:
            image_files = [img.imageUrl for img in dto.imageList]
            if contains_human_in_all_files(image_files):
                Mysql.log.warn(f"🚫 사람 포함 → 스킵: {dto.name}")
                # Mysql.log.warn("   📁 이미지 목록:")
                # for img in image_files:
                #     Mysql.log.warn(f"     - {img}")
                return False

        except Exception as e:
            Mysql.log.warn(f"⚠️ Vision 검사 오류: {e}")

        return True

    # INSERT popup
    @staticmethod
    def insert_popup(cursor, dto: PopupDTO):
        sql = """
        INSERT INTO popup (
            name, start_date, end_date,
            open_time, close_time,
            address, road_address,
            region, latitude, longitude,
            geocoding_query,
            insta_post_id, insta_post_url,
            caption_summary, caption,
            media_type, is_active,
            created_at, updated_at
        )
        VALUES (
            %(name)s, %(start_date)s, %(end_date)s,
            %(open_time)s, %(close_time)s,
            %(address)s, %(road_address)s,
            %(region)s, %(latitude)s, %(longitude)s,
            %(geocoding_query)s,
            %(insta_post_id)s, %(insta_post_url)s,
            %(caption_summary)s, %(caption)s,
            %(media_type)s, %(is_active)s,
            NOW(), NOW()
        )
        """

        cursor.execute(sql, {
            "name": dto.name,
            "start_date": dto.startDate,
            "end_date": dto.endDate,
            "open_time": dto.openTime,
            "close_time": dto.closeTime,
            "address": dto.address,
            "road_address": dto.roadAddress,
            "region": dto.region,
            "latitude": dto.latitude,
            "longitude": dto.longitude,
            "geocoding_query": dto.geocodingQuery,
            "insta_post_id": dto.instaPostId,
            "insta_post_url": dto.instaPostUrl,
            "caption_summary": dto.captionSummary,
            "caption": dto.caption,
            "media_type": dto.mediaType,
            "is_active": dto.isActive,
        })

        return cursor.lastrowid

    # INSERT popup_image
    @staticmethod
    def insert_images(cursor, popup_id, imageList: List[PopupImageDTO]):
        sql = """
        INSERT INTO popup_image (popup_id, image_url, sort_order)
        VALUES (%s, %s, %s)
        """

        for img in imageList:
            cursor.execute(sql, (popup_id, to_server_path(img.imageUrl), img.sortOrder))

    # 전체 실행 Flow
    @staticmethod
    def play(local: bool = True):
        load_dotenv()

        # 파일 읽기
        items = Mysql.file_open("geo.json")
        if not items: return

        # DB 연결
        conn = Mysql.connect_db(local=local)
        cursor = conn.cursor()

        success = []
        skipped = 0

        for item in items:
            dto = PopupDTO.to_dto(item)

            # Validation
            if not Mysql.validate(dto):
                skipped += 1
                continue

            try:
                # popup INSERT후 MySQL이 부여한 id를 반환
                popup_id = Mysql.insert_popup(cursor, dto)

                # uuid 조회
                cursor.execute("SELECT uuid FROM popup WHERE id=%s", (popup_id,))
                popup_uuid = cursor.fetchone()["uuid"]

                # popup_image INSERT
                Mysql.insert_images(cursor, popup_id, dto.imageList)
                conn.commit()

                # 저장 리스트에 추가
                success.append({
                    **item,
                    "popup_id": popup_id,
                    "popup_uuid": popup_uuid,
                })
                Mysql.log.info(f"✅ 삽입 완료: {dto.name}")

            except Exception as e:
                conn.rollback()
                skipped += 1
                Mysql.log.error(f"❌ 삽입 실패: {dto.name} → {e}")
        
        # 결과 저장
        Mysql.file_save(success, "mysql.json")
        Mysql.log.plain(f"🎉 완료: {len(success)}개 / 스킵 {skipped}개")
            
if __name__ == "__main__":
    Mysql.play(local=False)
