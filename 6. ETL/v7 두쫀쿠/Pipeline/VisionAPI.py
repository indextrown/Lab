import os
import requests

# -------------------------------------------------
# Logger import: main 실행 + 단독 실행 모두 지원
# -------------------------------------------------
try:
    from .Logger import Logger
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Logger import Logger

log = Logger("VisionAPI", use_color=False)

# -------------------------------------------------
# 🔥 Google Vision API Credentials 경로 통일
#    → 프로젝트 루트(V6)에서 항상 불러오도록 변경
# -------------------------------------------------
PROJECT_ROOT = os.getcwd()     # main.py 실행, Alert.py 실행 모두 통일
CREDENTIAL_PATH = os.path.join(PROJECT_ROOT, "poppang-475205-c9e6e178df72.json")

if not os.path.exists(CREDENTIAL_PATH):
    log.error(f"❌ Credential JSON 없음 → {CREDENTIAL_PATH}")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIAL_PATH

# Vision API import 이후 적용됨
from google.cloud import vision

client = vision.ImageAnnotatorClient(
    client_options={"api_endpoint": "vision.googleapis.com:443"}
)

# -------------------------------------------------
# 🙍 사람 감지 키워드
# -------------------------------------------------
HUMAN_KEYWORDS = [
    # 인물 기본
    "person", "people", "human", "face",

    # 성별·연령
    "man", "woman", "boy", "girl",
    "child", "kid", "baby", "toddler", "infant", "teenager",

    # 집단
    "crowd", "family", "group",
]

# ===============================================
# 🖼️ 로컬 이미지 한 장 검사
# ===============================================
def contains_human_file(image_path: str) -> bool:
    """로컬 이미지에서 사람 포함 여부 검사"""
    try:
        with open(image_path, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)

        # 얼굴 감지
        faces = client.face_detection(image=image).face_annotations
        if len(faces) > 0:
            log.warn(f"🚫 얼굴 감지됨 → {image_path}")
            return True

        # 라벨 감지
        labels = client.label_detection(image=image).label_annotations
        for label in labels:
            if any(k in label.description.lower() for k in HUMAN_KEYWORDS):
                log.warn(f"🚫 사람 관련 라벨 감지({label.description}) → {image_path}")
                return True

    except Exception as e:
        log.error(f"❌ Vision 오류 ({image_path}): {e}")

    return False


# ===============================================
# 🖼️ 로컬 여러 이미지 검사 (배치)
# ===============================================
def contains_human_in_all_files(image_paths: list[str], batch_size: int = 15) -> bool:
    if not image_paths:
        log.warn("❌ 이미지 리스트가 비어 있음")
        return False

    valid_paths = [p for p in image_paths if p.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not valid_paths:
        log.warn("❌ 유효한 이미지 없음 (확장자 필터링됨)")
        return False

    for i in range(0, len(valid_paths), batch_size):
        batch = valid_paths[i:i+batch_size]
        requests_list = []

        for path in batch:
            try:
                with open(path, "rb") as f:
                    content = f.read()

                image = vision.Image(content=content)
                requests_list.append(
                    vision.AnnotateImageRequest(
                        image=image,
                        features=[
                            vision.Feature(type=vision.Feature.Type.FACE_DETECTION),
                            vision.Feature(type=vision.Feature.Type.LABEL_DETECTION)
                        ]
                    )
                )
            except Exception as e:
                log.error(f"❌ 파일 읽기 오류: {path} → {e}")

        response = client.batch_annotate_images(requests=requests_list)

        for idx, res in enumerate(response.responses):
            file_path = batch[idx]

            if res.error.message:
                log.error(f"❌ Vision 오류({file_path}): {res.error.message}")
                continue

            # 얼굴 감지
            if len(res.face_annotations) > 0:
                log.warn(f"🚫 얼굴 감지됨 → {file_path}")
                return True

            # 라벨 감지
            for label in res.label_annotations:
                if any(k in label.description.lower() for k in HUMAN_KEYWORDS):
                    log.warn(f"🚫 사람 라벨({label.description}) → {file_path}")
                    return True

    return False


# ===============================================
# 🌐 URL 이미지 검사
# ===============================================
def contains_human_url(url: str) -> bool:
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            log.warn(f"❌ URL 다운로드 실패: {url}")
            return False

        image = vision.Image(content=resp.content)

        faces = client.face_detection(image=image).face_annotations
        if len(faces) > 0:
            log.warn(f"🚫 얼굴 감지됨(URL) → {url}")
            return True

        labels = client.label_detection(image=image).label_annotations
        for label in labels:
            if any(k in label.description.lower() for k in HUMAN_KEYWORDS):
                log.warn(f"🚫 사람 라벨(URL → {label.description}) → {url}")
                return True

    except Exception as e:
        log.error(f"❌ Vision 오류(URL={url}): {e}")

    return False


# ===============================================
# 🌐 URL 여러 개 검사 (배치)
# ===============================================
def contains_human_in_all_urls(urls: list[str]) -> bool:
    valid_urls = []
    reqs = []

    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                log.warn(f"❌ URL 다운로드 실패: {url}")
                continue

            reqs.append(
                vision.AnnotateImageRequest(
                    image=vision.Image(content=resp.content),
                    features=[
                        vision.Feature(type=vision.Feature.Type.FACE_DETECTION),
                        vision.Feature(type=vision.Feature.Type.LABEL_DETECTION)
                    ]
                )
            )
            valid_urls.append(url)

        except Exception as e:
            log.error(f"❌ URL 접근 실패: {url} → {e}")

    if not reqs:
        return False

    response = client.batch_annotate_images(requests=reqs)

    for idx, res in enumerate(response.responses):
        url = valid_urls[idx]

        if res.error.message:
            log.error(f"❌ Vision 오류(URL={url}): {res.error.message}")
            continue

        if len(res.face_annotations) > 0:
            log.warn(f"🚫 얼굴 감지됨(URL) → {url}")
            return True

        for label in res.label_annotations:
            if any(k in label.description.lower() for k in HUMAN_KEYWORDS):
                log.warn(f"🚫 사람 라벨(URL → {label.description}) → {url}")
                return True

    return False



# ===================================
# 🧪 테스트
# ===================================
if __name__ == "__main__":
    # ✅ 로컬 단일 테스트
    # local_file = "sample.jpg"
    # print(f"[로컬 1개] {contains_human_file(local_file)}")

    # # ✅ 로컬 여러 개 테스트
    # local_list = ["sample.jpg", "sample2.jpg"]
    # print(f"[로컬 여러 개] {contains_human_in_all_files(local_list)}")

    # ✅ URL 단일 테스트
    # url_file = "https://scontent-icn2-1.cdninstagram.com/v/t51.82787-15/565417090_17864747205473410_3126136565006634466_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=108&ccb=1-7&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=hd8y4X23JGMQ7kNvwFwRexL&_nc_oc=AdnE1KUZNxyhYYZ5KKjcCMvvZR2oBDHXJ5WAQwkKJaoNpizxm4AGoqBIbxzXYskWuPc&_nc_zt=23&_nc_ht=scontent-icn2-1.cdninstagram.com&edm=AEoDcc0EAAAA&_nc_gid=GlzyGCrbEDWlbvWdep2TBQ&oh=00_Afc-KMxIrJpYK3iefhT3xW3tmuXibVXHazGyxSjcX7873g&oe=68F5AFC0"
    # print(f"[URL 1개] {contains_human_url(url_file)}")

    # # ✅ URL 여러 개 테스트
    url_list = [
        "https://scontent-icn2-1.cdninstagram.com/v/t51.82787-15/565417090_17864747205473410_3126136565006634466_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=108&ccb=1-7&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=hd8y4X23JGMQ7kNvwFwRexL&_nc_oc=AdnE1KUZNxyhYYZ5KKjcCMvvZR2oBDHXJ5WAQwkKJaoNpizxm4AGoqBIbxzXYskWuPc&_nc_zt=23&_nc_ht=scontent-icn2-1.cdninstagram.com&edm=AEoDcc0EAAAA&_nc_gid=GlzyGCrbEDWlbvWdep2TBQ&oh=00_Afc-KMxIrJpYK3iefhT3xW3tmuXibVXHazGyxSjcX7873g&oe=68F5AFC0",
        "https://scontent-icn2-1.cdninstagram.com/v/t51.82787-15/565417090_17864747205473410_3126136565006634466_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=108&ccb=1-7&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=hd8y4X23JGMQ7kNvwFwRexL&_nc_oc=AdnE1KUZNxyhYYZ5KKjcCMvvZR2oBDHXJ5WAQwkKJaoNpizxm4AGoqBIbxzXYskWuPc&_nc_zt=23&_nc_ht=scontent-icn2-1.cdninstagram.com&edm=AEoDcc0EAAAA&_nc_gid=GlzyGCrbEDWlbvWdep2TBQ&oh=00_Afc-KMxIrJpYK3iefhT3xW3tmuXibVXHazGyxSjcX7873g&oe=68F5AFC0"
    ]
    print(f"[URL 여러 개] {contains_human_in_all_urls(url_list)}")








