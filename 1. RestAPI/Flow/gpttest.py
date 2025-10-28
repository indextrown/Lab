import os
from openai import OpenAI
from dotenv import load_dotenv

# ✅ .env에서 GPT 키 불러오기
load_dotenv()
GPT_ACCESS_TOKEN = os.getenv("GPT_ACCESS_TOKEN")

if not GPT_ACCESS_TOKEN:
    raise ValueError("❌ GPT_ACCESS_TOKEN이 .env에서 로드되지 않았습니다!")

# ✅ GPT 클라이언트 생성
client = OpenAI(api_key=GPT_ACCESS_TOKEN)

def gpt_check_human(image_url: str) -> bool:
    """
    GPT API로 이미지 내 사람 존재 여부 확인
    """
    prompt = "이 이미지 안에 사람이 있습니까? 사람이 조금이라도 보이면 'YES', 없으면 'NO'만 답하세요."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Vision 기능 지원 모델
            messages=[
                {"role": "system", "content": "당신은 이미지 분석가입니다."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ]
        )

        answer = response.choices[0].message.content.strip().upper()
        print(f"🤖 GPT 판별 결과 (url={image_url}): {answer}")

        return "YES" in answer
    except Exception as e:
        print(f"❌ GPT 판별 실패 (url={image_url}): {e}")
        return False

def check_human_in_all_images(image_urls: list[str]) -> bool:
    """
    여러 장의 이미지에서 사람 존재 여부를 검사
    하나라도 사람이 감지되면 True 반환
    """
    has_human = False
    for url in image_urls:
        if gpt_check_human(url):
            has_human = True
    return has_human

if __name__ == "__main__":
    # ✅ URL 여러 개 생성
    url_list = []
    for i in range(1, 12+1):
        base_url = f"https://poppang.co.kr/images/20251022-203046_18006553517650048/%EC%BF%A0%ED%82%A4%EB%9F%B0__%EB%85%B8%EB%A5%B4%EB%94%94%EC%8A%A4%ED%81%AC_%EC%BF%A0%ED%82%A4%EC%BA%A0%ED%94%84_{i}.jpg"
        url_list.append(base_url)
        print(base_url)

    # ✅ 전체 이미지에서 사람 존재 여부 체크
    result = check_human_in_all_images(url_list)
    print(f"[URL 여러 개 결과] {'🚨 사람 감지됨' if result else '✅ 사람 없음'}")
