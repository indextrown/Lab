import os
import requests
import base64
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
                    vision.Feature(type=vision.Feature.Type.LABEL_DETECTION),
                    vision.Feature(type=vision.Feature.Type.OBJECT_LOCALIZATION)
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

        # 👀 얼굴 탐지 결과 출력
        if len(res.face_annotations) > 0:
            print(f"🚫 얼굴 감지됨: {valid_urls[idx]} (감지된 얼굴 수: {len(res.face_annotations)})")
            return True

        # 👀 라벨 감지 결과 전체 출력
        print(f"📝 라벨 감지 결과 (url={valid_urls[idx]}):")
        for label in res.label_annotations:
            print(f"  - {label.description} (score={label.score:.2f})")

        # 👮 사람 관련 라벨 여부 판별
        for label in res.label_annotations:
            if any(keyword in label.description.lower() for keyword in HUMAN_KEYWORDS):
                print(f"🚫 사람 관련 라벨 감지됨: {valid_urls[idx]} ({label.description})")
                return True

    return False







# ===================================
# 🧪 테스트
# ===================================
if __name__ == "__main__":

    # # ✅ URL 여러 개 테스트
    url_list = [
        "https://scontent-icn2-1.cdninstagram.com/v/t51.82787-15/565417090_17864747205473410_3126136565006634466_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=108&ccb=1-7&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=hd8y4X23JGMQ7kNvwFwRexL&_nc_oc=AdnE1KUZNxyhYYZ5KKjcCMvvZR2oBDHXJ5WAQwkKJaoNpizxm4AGoqBIbxzXYskWuPc&_nc_zt=23&_nc_ht=scontent-icn2-1.cdninstagram.com&edm=AEoDcc0EAAAA&_nc_gid=GlzyGCrbEDWlbvWdep2TBQ&oh=00_Afc-KMxIrJpYK3iefhT3xW3tmuXibVXHazGyxSjcX7873g&oe=68F5AFC0",
        "https://scontent-icn2-1.cdninstagram.com/v/t51.82787-15/565417090_17864747205473410_3126136565006634466_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=108&ccb=1-7&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=hd8y4X23JGMQ7kNvwFwRexL&_nc_oc=AdnE1KUZNxyhYYZ5KKjcCMvvZR2oBDHXJ5WAQwkKJaoNpizxm4AGoqBIbxzXYskWuPc&_nc_zt=23&_nc_ht=scontent-icn2-1.cdninstagram.com&edm=AEoDcc0EAAAA&_nc_gid=GlzyGCrbEDWlbvWdep2TBQ&oh=00_Afc-KMxIrJpYK3iefhT3xW3tmuXibVXHazGyxSjcX7873g&oe=68F5AFC0"
    ]


    
    url_list = []
    for i in range(1, 2+1):
        base_url = f"https://poppang.co.kr/images/20251022-203046_18006553517650048/%EC%BF%A0%ED%82%A4%EB%9F%B0__%EB%85%B8%EB%A5%B4%EB%94%94%EC%8A%A4%ED%81%AC_%EC%BF%A0%ED%82%A4%EC%BA%A0%ED%94%84_{i}.jpg"
        url_list.append(base_url)
        print(base_url)
    print(f"[URL 여러 개] {contains_human_in_all_urls(url_list)}")
