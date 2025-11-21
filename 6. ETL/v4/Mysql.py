import os
import json
import pymysql
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import VisionAPI
from Logger import Logger


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
# 🧭 Util
# ==============================
def build_image_list(image_paths: List[str]) -> List[PopupImageDTO]:
    return [
        PopupImageDTO(
            imageUrl=path,
            sortOrder=i,
        )
        for i, path in enumerate(image_paths)
    ]

def to_server_path(local_path: str) -> str:
    """
    절대경로(/Users/...) → /images/... 로 변환
    """
    if "/images/" in local_path:
        return local_path[local_path.index("/images/"):]
    return local_path

def build_payload(item: dict) -> PopupUploadDTO:
    image_paths = item.get("image_paths", [])
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
        imageList=build_image_list(image_paths),
        recommendIdList=item.get("recommend", []),
    )


# ==============================
# 🐬 Mysql 업로드 클래스
# ==============================
class Mysql:
    log = Logger("Mysql")

    @staticmethod
    def play(local: bool = True):
        # 📌 환경 변수 로드
        load_dotenv()

        # 📌 JSON 파일 지정
        geo_path = os.path.join(os.getcwd(), "geo.json")
        if not os.path.exists(geo_path):
            Mysql.log.error("❌ geo.json 없음")
            return

        with open(geo_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 📌 DB 연결
        host = "127.0.0.1" if local else os.getenv("DB_HOST")

        # 📌 DB 연결
        conn = pymysql.connect(
            host=host,
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        cursor = conn.cursor()

        success_list = []
        total = len(data)
        inserted = 0
        skipped = 0
        human_skipped = 0

        for item in data:
            dto = build_payload(item)

            # ===== Vision 검사 =====
            if dto.mediaType == "VIDEO":
                skipped += 1
                continue

            has_human = False
            try:
                if dto.imageList:
                    has_human = VisionAPI.contains_human_in_all_files(
                        [img.imageUrl for img in dto.imageList]
                    )
            except Exception as e:
                Mysql.log.error(f"Vision 오류: {e}")
                skipped += 1
                continue

            if has_human:
                human_skipped += 1
                continue

            # ===== popup INSERT =====
            try:
                insert_sql = """
                INSERT INTO popup (
                    name, start_date, end_date,
                    open_time, close_time,
                    address, road_address,
                    region, latitude, longitude,
                    geocoding_query,
                    insta_post_id, insta_post_url,
                    caption_summary, caption,
                    media_type, is_active
                )
                VALUES (
                    %(name)s, %(start_date)s, %(end_date)s,
                    %(open_time)s, %(close_time)s,
                    %(address)s, %(road_address)s,
                    %(region)s, %(latitude)s, %(longitude)s,
                    %(geocoding_query)s,
                    %(insta_post_id)s, %(insta_post_url)s,
                    %(caption_summary)s, %(caption)s,
                    %(media_type)s, %(is_active)s
                )
                """

                cursor.execute(insert_sql, {
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

                conn.commit()

                popup_id = cursor.lastrowid
                # uuid는 DB가 자동 생성 → 바로 SELECT
                cursor.execute("SELECT uuid FROM popup WHERE id=%s", (popup_id,))
                popup_uuid = cursor.fetchone()["uuid"]

            except Exception as e:
                Mysql.log.error(f"❌ popup INSERT 실패: {e}")
                conn.rollback()
                skipped += 1
                continue

            # ===== popup_image INSERT =====
            try:
                img_sql = """
                INSERT INTO popup_image (popup_id, image_url, sort_order)
                VALUES (%s, %s, %s)
                """
                for img in dto.imageList:
                    cursor.execute(img_sql, (popup_id, to_server_path(img.imageUrl), img.sortOrder))

                conn.commit()
            except Exception as e:
                Mysql.log.error(f"❌ popup_image INSERT 실패: {e}")
                conn.rollback()
                skipped += 1
                continue

            # ===== 성공한 데이터 mysql.json에 저장될 리스트에 추가 =====
            success_list.append({
                **item,
                "popup_id": popup_id,
                "popup_uuid": popup_uuid,
            })

            inserted += 1
            Mysql.log.info(f"📌 업로드 완료 popup_id={popup_id}, insta={dto.instaPostId}")

        # ===== mysql.json 저장 =====
        out_path = os.path.join(os.getcwd(), "mysql.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(success_list, f, ensure_ascii=False, indent=2)

        Mysql.log.plain(f"✅ 업로드 완료 {inserted}/{total}")
        Mysql.log.plain(f"🚫 Vision 필터: {human_skipped}")
        Mysql.log.plain(f"⚠️ 기타 스킵: {skipped}")

        conn.close()


# ==============================
# 🏁 실행
# ==============================
if __name__ == "__main__":
    Mysql.play(local=True)
