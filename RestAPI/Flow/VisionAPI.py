import os
import requests

# ✅ DNS 회피 설정
os.environ["GRPC_DNS_RESOLVER"] = "native"
os.environ["GRPC_ENABLE_FEDERATION"] = "0"
os.environ["GRPC_DNS_ENABLE_SRV_QUERY"] = "0"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "poppang-475205-c9e6e178df72.json"
from google.cloud import vision

# ✅ 절대 경로로 Credential 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "poppang-475205-c9e6e178df72.json")

client = vision.ImageAnnotatorClient(
    client_options={"api_endpoint": "vision.googleapis.com:443"}
)

# ✅ 사람이 포함됐는지 판별할 키워드 목록
HUMAN_KEYWORDS = [
    # 인물 기본
    "person", "people", "human", "face",

    # 성별·연령
    "man", "woman", "boy", "girl",
    "child", "kid", "baby", "toddler", "infant", "teenager",

    # 집단
    "crowd", "family", "group",
]

# ===================================
# 🖼️ 1. 로컬 이미지 1개 검사
# ===================================
def contains_human_file(image_path: str) -> bool:
    """로컬 이미지 1개에서 사람 감지"""
    try:
        with open(image_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)

        # 얼굴 감지
        faces = client.face_detection(image=image).face_annotations
        if len(faces) > 0:
            return True

        # 라벨 감지
        labels = client.label_detection(image=image).label_annotations
        for label in labels:
            if any(keyword in label.description.lower() for keyword in HUMAN_KEYWORDS):
                return True

    except Exception as e:
        print(f"❌ Vision API 오류 (file: {image_path}): {e}")
    return False


# ===================================
# 🖼️ 2. 로컬 이미지 여러 개 검사 (배치 처리 개선)
# ===================================
def contains_human_in_all_files(image_paths: list[str], batch_size: int = 15) -> bool:
    if not image_paths:
        print("❌ 이미지 경로가 비어 있음")
        return False

    # ✅ 이미지 확장자 필터링 (mp4 등 제거)
    valid_paths = [p for p in image_paths if p.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not valid_paths:
        print("❌ 유효한 이미지 파일이 없음")
        return False

    # ✅ 배치 단위로 Vision API 요청
    for i in range(0, len(valid_paths), batch_size):
        batch = valid_paths[i:i+batch_size]
        requests_list = []

        for path in batch:
            try:
                with open(path, "rb") as f:
                    content = f.read()
                image = vision.Image(content=content)
                annotate_request = vision.AnnotateImageRequest(
                    image=image,
                    features=[
                        vision.Feature(type=vision.Feature.Type.FACE_DETECTION),
                        vision.Feature(type=vision.Feature.Type.LABEL_DETECTION)
                    ]
                )
                requests_list.append(annotate_request)
            except Exception as e:
                print(f"❌ 로컬 파일 읽기 오류: {path}, {e}")

        response = client.batch_annotate_images(requests=requests_list)

        for idx, res in enumerate(response.responses):
            if res.error.message:
                print(f"❌ Vision API 오류 (file={batch[idx]}): {res.error.message}")
                continue

            if len(res.face_annotations) > 0:
                print(f"🚫 사람 감지됨: {batch[idx]}")
                return True

            for label in res.label_annotations:
                if any(keyword in label.description.lower() for keyword in HUMAN_KEYWORDS):
                    print(f"🚫 라벨 감지됨(사람 관련): {batch[idx]} ({label.description})")
                    return True

    return False

# ===================================
# 🌐 3. URL 이미지 1개 검사
# ===================================
def contains_human_url(image_url: str) -> bool:
    """URL 1개에서 사람 감지"""
    try:
        resp = requests.get(image_url, timeout=10)
        if resp.status_code != 200:
            print(f"❌ 이미지 다운로드 실패: {image_url}")
            return False

        content = resp.content
        image = vision.Image(content=content)

        faces = client.face_detection(image=image).face_annotations
        if len(faces) > 0:
            return True

        labels = client.label_detection(image=image).label_annotations
        for label in labels:
            if any(keyword in label.description.lower() for keyword in HUMAN_KEYWORDS):
                return True

    except Exception as e:
        print(f"❌ Vision API 오류 (url: {image_url}): {e}")
    return False


# ===================================
# 🌐 4. URL 이미지 여러 개 검사 (배치 처리)
# ===================================
def contains_human_in_all_urls(image_urls: list[str]) -> bool:
    if not image_urls:
        print("❌ URL 리스트가 비어 있음")
        return False

    requests_list = []
    valid_urls = []   # 다운로드 성공한 URL만 따로 저장

    for url in image_urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"❌ 이미지 다운로드 실패: {url}")
                continue

            image = vision.Image(content=resp.content)
            annotate_request = vision.AnnotateImageRequest(
                image=image,
                features=[
                    vision.Feature(type=vision.Feature.Type.FACE_DETECTION),
                    vision.Feature(type=vision.Feature.Type.LABEL_DETECTION)
                ]
            )
            requests_list.append(annotate_request)
            valid_urls.append(url)

        except Exception as e:
            print(f"❌ URL 요청 실패: {url}, {e}")

    if not requests_list:
        print("❌ 유효한 URL 이미지가 없음")
        return False

    response = client.batch_annotate_images(requests=requests_list)

    for idx, res in enumerate(response.responses):
        if res.error.message:
            print(f"❌ Vision API 오류 (url={valid_urls[idx]}): {res.error.message}")
            continue

        if len(res.face_annotations) > 0:
            print(f"🚫 사람 감지됨: {valid_urls[idx]}")
            return True

        for label in res.label_annotations:
            if any(keyword in label.description.lower() for keyword in HUMAN_KEYWORDS):
                print(f"🚫 라벨 감지됨(사람 관련): {valid_urls[idx]} ({label.description})")
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

    num = 1
    base_url = f"https://poppang.co.kr/images/20251022-203046_18006553517650048/%EC%BF%A0%ED%82%A4%EB%9F%B0__%EB%85%B8%EB%A5%B4%EB%94%94%EC%8A%A4%ED%81%AC_%EC%BF%A0%ED%82%A4%EC%BA%A0%ED%94%84_{num}.jpg"
    url_list = []
    for i in range(1, 12+1):
        url_list.append(base_url)
        print(base_url)
        num += 1
    print(f"[URL 여러 개] {contains_human_in_all_urls(url_list)}")