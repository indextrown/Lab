import os
import re
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List, Optional

# ==============================
# 📊 카테고리 매핑
# ==============================
CATEGORY_MAP = {
    "기타": 99,
    "패션": 1,
    "뷰티": 2,
    "디저트": 3,
    "카페": 4,
    "주류": 5,
    "IT": 6,
    "생활용품": 7,
    "스포츠": 8,
    "영화": 9,
    "애니메이션": 10,
    "웹툰": 11,
    "연예인": 12,
    "문화/예술": 13,
    "여행": 14,
    "반려동물": 15,
    "게임": 16,
    "책": 17,
    "금융": 18,
    "친환경": 19,
    "키즈": 20
}

def convert_recommend_to_ids(recommend_list: List[str]) -> List[int]:
    ids = [CATEGORY_MAP[name] for name in recommend_list if name in CATEGORY_MAP]
    if not ids:
        ids = [0]  # 기본값: 기타
    return ids


# ==============================
# 📦 DTO 정의
# ==============================

@dataclass
class InstagramPostDTO:
    """📸 Instagram 원본 데이터"""
    id: str
    caption: str
    media_type: str
    permalink: str
    media_urls: List[str]

@dataclass
class GptParsedEventDTO:
    """🧠 GPT 파싱 결과"""
    name: str
    start_date: str
    end_date: str
    open_time: str
    close_time: str
    address: str
    region: str
    geocoding_query: str
    caption_summary: str
    recommend: list[str]
    section: Optional[int] = None

@dataclass
class PopupEventDTO:
    """📌 최종 병합 결과"""
    name: str
    start_date: str
    end_date: str
    open_time: str
    close_time: str
    address: str
    region: str
    geocoding_query: str
    insta_post_id: str
    insta_post_url: str
    caption_summary: str
    caption: str
    image_url: List[str]
    image_paths: List[str]
    media_type: str
    recommend: List[int]


# ==============================
# 🧠 GPT 파이프라인
# ==============================

class GptAPI:
    REQUIRED_FIELDS = ["name", "start_date", "end_date", "address", "region", "caption_summary", "recommend"]  # ✅ 추가
    def __init__(self, access_token, model="gpt-4o-mini"):
        self.access_token = access_token
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        })

    # ---------- 문자열 정제 ----------
    @staticmethod
    def slugify(text: str) -> str:
        if not text:
            return "no_name"
        text = text.strip()
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'[^\w\-가-힣]', '', text)
        return text

    # ---------- 파일 입출력 ----------
    def file_open(self, filename: str) -> List[InstagramPostDTO]:
        with open(filename, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        posts: List[InstagramPostDTO] = []
        for item in raw_data:
            posts.append(
                InstagramPostDTO(
                    id=item.get("id", ""),
                    caption=item.get("caption", ""),
                    media_type=item.get("media_type", ""),
                    permalink=item.get("permalink", ""),
                    media_urls=item.get("media_urls", []),
                )
            )
        return posts

    def file_save(self, data: List[PopupEventDTO]):
        path = "gpt.json"
        json_data = [obj.__dict__ for obj in data]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"📁 저장 완료: {os.path.abspath(path)}")
        return os.path.abspath(path)

    # ---------- GPT 프롬프트 (원문 유지) ----------
    def build_prompt(self, sections):
        lines = []
        for idx, cap in sections:
            lines.append(f"[section {idx}]\n{cap}")
        body = "\n\n---\n\n".join(lines)

        # ✅ 여기서 required_fields 문자열화
        required_list_str = ", ".join(self.REQUIRED_FIELDS)
        categories_str = ", ".join(CATEGORY_MAP.keys())

        return f"""
        아래에는 여러 개의 '섹션' 텍스트가 주어집니다.
        각 섹션에는 하나 이상의 팝업 이벤트 정보가 포함될 수 있습니다.

        각 팝업 이벤트에 대해 다음 **소문자 키**만 포함된 객체를 생성하고,
        모든 객체를 **JSON 배열**로 반환하세요.

        ─────────────────────────────
        📌 필드별 작성 규칙
        ─────────────────────────────

        - name: 팝업 이름 또는 행사명

        - start_date: 시작 날짜 (YYYY-MM-DD 형식)

        - end_date: 종료 날짜 (YYYY-MM-DD 형식)

        - open_time: 운영 시작 시간 (HH:MM)

        - close_time: 운영 종료 시간 (HH:MM)

        - address: 도로명 주소 또는 건물명
            - ⚠️ address가 추출되지 않는 경우, 이 이벤트는 JSON에 포함하지 마세요.

        - region: 지역명 (예: 서울, 부산, 도쿄)
            - ⚠️ region이 누락되면 이 이벤트는 JSON에 포함하지 마세요.

        - geocoding_query: address와 region, name을 기반으로 지오코딩 API 검색에 최적화된 문자열
            1) 지역(region)을 반드시 가장 앞에 붙이세요. (예: '부산', '서울', '성남')
            2) address 또는 name에서 건물명, 공간명 등의 핵심 지명 요소만 붙이세요.
            - 예: "성남 현대백화점 판교" ✅
            - 예: "성남 현대백화점 판교 도씨" ❌ (브랜드명 제거)
            3) 층수, 방향, 조사 등 불필요한 단어는 제거하세요:
            - 'B1', '1층', '2F', 'B2F', '지하 1층'
            - '앞', '근처', '맞은편', '옆', '뒷편', '앞쪽', '뒤편'
            - '~에서', '~앞', '~근처', '~맞은편'
            4) 브랜드명, 팝업 이름, 아티스트 이름, 제품 이름 등은 반드시 제거하세요.
            - 예: "서울 신촌유플렉스 후르츠바스켓" → "서울 신촌유플렉스"
            - 예: "서울 현대백화점 압구정본점 김재중" → "서울 현대백화점 압구정본점"
            - 예: "부산 신세계백화점 스타필드 팝업스토어" → "부산 신세계백화점 스타필드"
            5) 팝업명과 address가 동일하더라도 브랜드명은 제거해야 합니다.
            6) 브랜드명이 제거된 후에도 최소한 지역 + 건물명/지명은 반드시 포함되어야 합니다.
            7) address가 없는 경우 name에서 지명/건물명만 추출하세요. 브랜드명은 포함하지 마세요.
            8) 단순히 지역명만 쓰는 것은 금지입니다. (예: "성남" ❌)
            반드시 "성남 현대백화점 판교"처럼 구체적인 지명까지 포함하세요.
            9) 문장형이 아니라 짧고 검색 최적화된 명사구로 작성하세요.

        - section: 이 이벤트가 추출된 섹션 번호(정수)

        - caption_summary: "caption_summary는 단순 요약이 아니라, 인스타 원문을 기반으로 한 완성된 게시글형 문단입니다. \
            ✨ 구성 규칙:\n
            - 전체는 약 6~10줄로 구성하세요.
            - 상단에는 팝업 이름, 위치, 일정, 운영시간을 간결히 표시하세요.
            - 하단에는 팝업의 분위기, 전시·체험 내용, 운영 특징 등을 자연스럽게 3줄 이상으로 설명하세요.
            - 문장은 짧고 자연스럽게, 말하듯이 표현하세요.
            - 감성적인 표현은 허용하지만, 과장되거나 홍보성 어투는 피하세요.
            - 문장 사이에는 줄바꿈(\\n)을 포함하세요.
            예시:\\n
            🥐 Jam in Bread 팝업스토어 오픈\\n
            📍 신세계백화점 강남점 B1\\n
            📅 10.7(월) ~ 10.13(일)\\n
            🕥 10:30AM ~ 8:00PM\\n
            \\n
            따뜻한 향이 퍼지는 공간에서 잼과 빵을 함께 즐길 수 있습니다.\\n
            다양한 수제잼과 베이커리 굿즈가 전시되어 있고, 일부 상품은 현장 구매도 가능합니다.\\n
            하루의 시작을 부드럽게 채워주는 작은 휴식 같은 팝업입니다.\\n"

        - recommend : 아래 목록 중에서 관련된 팝업 카테고리를 **1개 이상, 최대 3개까지** 선택하여 배열로 반환하세요.
            - [{categories_str}]
            📌 **선택 기준**:
                1) 캡션 또는 팝업 이름에서 핵심 키워드를 추출하여 가장 연관성이 높은 카테고리를 우선 선택하세요.
                - 예: "스타벅스", "카페", "커피", "음료" → "카페"
                - 예: "한정판 스니커즈", "신발", "옷", "패션쇼" → "패션"
                - 예: "맥주", "위스키", "칵테일" → "주류"
                - 예: "팝콘", "상영", "영화관" → "영화"
                - 예: "애니", "만화", "코스프레" → "애니메이션"
                - 예: "웹툰", "네이버웹툰", "작가전" → "웹툰"
                - 예: "팬사인회", "가수", "아이돌", "팬미팅" → "연예인"
                - 예: "여행", "관광", "숙소", "항공", "해외" → "여행"
                - 예: "강아지", "고양이", "반려동물" → "반려동물"
                - 예: "게임", "콘솔", "PC방", "플레이" → "게임"
                - 예: "책", "북카페", "서점" → "책"
                - 예: "금융", "은행", "카드", "투자" → "금융"
                - 예: "에코", "환경", "제로웨이스트" → "친환경"
                - 예: "키즈", "어린이", "유아" → "키즈"
                - 예: "의류", "가방", "악세서리" → "패션"
                - 예: "화장품", "향수", "메이크업" → "뷰티"
                - 예: "케이크", "쿠키", "초콜릿" → "디저트"
                - 예: "커피", "음료", "티룸" → "카페"
                - 예: "테크", "스마트폰", "전자기기" → "IT"
                - 예: "리빙", "인테리어", "가구" → "생활용품"
                - 예: "운동", "러닝", "스포츠브랜드" → "스포츠"
                - 예: "전시회", "아트", "페어", "체험" → "문화/예술"

                2) 키워드가 두 가지 이상 관련될 경우 복수 선택 가능 (최대 3개).
                - 예: “디저트 카페” → ["디저트", "카페"]

                3) 관련 카테고리를 찾을 수 없을 경우에만 "기타"를 선택하세요.
                - 단순히 아무 키워드를 찾지 못했다고 해서 무조건 "기타"를 넣지 마세요.
                - 브랜드명, 제품군, 팝업 테마를 근거로 적극적으로 판단하세요.

            📌 **반환 형식 예시**:
                - recommend: ["패션"]
                - recommend: ["카페", "디저트"]
                - recommend: ["친환경", "패션", "카페"]
                - recommend: ["기타"]


        ─────────────────────────────
        ❗ 포함 기준
        ─────────────────────────────
        - 반드시 다음 필드들이 모두 존재해야 합니다:
        {required_list_str}
        - 위 필드 중 하나라도 누락된 이벤트는 JSON에 포함하지 마세요.
        → 불명확하거나 주소/날짜가 없는 이벤트는 제외하세요.

        ─────────────────────────────
        📅 날짜 규칙
        ─────────────────────────────
        - '10/7~10/23'처럼 월/일만 있으면 2025년으로 보완하세요.
        - 과거년도(2023, 2024 등)가 명시되어 있으면 그대로 사용하세요.
        - 모호한 날짜는 제외하세요.

        ─────────────────────────────
        🕒 시간 규칙
        ─────────────────────────────
        - '10:00~20:00' 형태는 open_time / close_time으로 나누세요.
        - 명시 없으면 빈 문자열로 둡니다.

        ─────────────────────────────
        🖼 이미지 규칙
        ─────────────────────────────
        - 이미지가 여러 장이면 배열 형태로 반환하세요.
        - 단일 이미지도 배열로 감싸서 반환하세요.

        ─────────────────────────────
        ⚠️ 출력 형식
        ─────────────────────────────
        - 반드시 JSON 배열([])만. 설명/주석/코드블록 금지.

        {body}
        """


    # ---------- GPT 호출 ----------
    def call_gpt(self, prompt, max_tokens=1500, retries=2):
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "너는 텍스트에서 구조화된 정보를 추출하는 전문가야."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens
        }
        for attempt in range(retries + 1):
            try:
                resp = self.session.post(self.endpoint, json=payload, timeout=60)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    print(f"⚠️ 응답 오류: {resp.status_code}")
                time.sleep(1)
            except requests.RequestException as e:
                print(f"⚠️ 요청 실패: {e}")
                time.sleep(1)
        raise RuntimeError("❌ GPT 응답 실패")

    # ---------- GPT 결과 파싱 ----------
    def extract_json_array(self, text) -> List[GptParsedEventDTO]:
        code_match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
        candidate = code_match.group(1) if code_match else self._greedy_bracket_slice(text)
        try:
            data = json.loads(candidate)
            return self._normalize_schema(data)
        except json.JSONDecodeError:
            return []

    def _normalize_schema(self, data) -> List[GptParsedEventDTO]:
        if not isinstance(data, list):
            return []
        parsed = []
        for obj in data:
            if "recommend" not in obj:
                print(f"⚠️ recommend 누락 → {obj.get('name')}")
            recommend_list = obj.get("recommend") or ["기타"]
            parsed.append(
                GptParsedEventDTO(
                    name=(obj.get("name") or "").strip(),
                    start_date=(obj.get("start_date") or "").strip(),
                    end_date=(obj.get("end_date") or "").strip(),
                    open_time=(obj.get("open_time") or "").strip(),
                    close_time=(obj.get("close_time") or "").strip(),
                    address=(obj.get("address") or "").strip(),
                    region=(obj.get("region") or "").strip(),
                    geocoding_query=(obj.get("geocoding_query") or "").strip(),
                    caption_summary=(obj.get("caption_summary") or "").strip(),
                    recommend=recommend_list,
                    section=int(obj["section"]) if obj.get("section") is not None else None
                )
            )
        return parsed

    def _greedy_bracket_slice(self, text):
        start, end = text.find("["), text.rfind("]")
        return text[start:end + 1] if start != -1 and end != -1 else "[]"
    
    # ---------- 필수 필드 필터 ----------
    def filter_required_fields(self, events: List[PopupEventDTO]) -> List[PopupEventDTO]:
        valid = []
        for e in events:
            missing = []
            for f in self.REQUIRED_FIELDS:
                value = getattr(e, f, "")
                # 문자열일 경우 공백 체크
                if isinstance(value, str) and not value.strip():
                    missing.append(f)
                # 리스트일 경우 비어있는지 체크
                elif isinstance(value, list) and len(value) == 0:
                    missing.append(f)

            if missing:
                print(f"⚠️ 필수 필드 누락({missing}) → {e.name or '이름 없음'} 제외")
                continue

            valid.append(e)
        return valid

    # ---------- 원본 데이터 병합 ----------
    def _enrich_with_original(self, posts: List[InstagramPostDTO], extracted: List[GptParsedEventDTO], section_to_post):
        results: List[PopupEventDTO] = []
        for event in extracted:
            orig = section_to_post.get(event.section, InstagramPostDTO("", "", "", "", []))
            recommend_ids = convert_recommend_to_ids(event.recommend)  # ✅ 문자열 → 정수 변환

            print("디버깅: recommend 문자열:", event.recommend, "→ recommend IDs:", recommend_ids)
            results.append(
                PopupEventDTO(
                    name=event.name,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    open_time=event.open_time,
                    close_time=event.close_time,
                    address=event.address,
                    region=event.region,
                    geocoding_query=event.geocoding_query,
                    insta_post_id=orig.id,
                    insta_post_url=orig.permalink,
                    caption_summary=event.caption_summary,
                    caption=orig.caption,
                    image_url=orig.media_urls,
                    image_paths=[],  # 다운로드 후 채워짐
                    media_type=orig.media_type,
                    recommend=recommend_ids   # ✅ 여기서 int 배열로 변환 완료
                )
            )
        return results

    # ---------- 이미지 다운로드 ----------
    def download_images(self, event: PopupEventDTO, base_dir="images"):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name_slug = self.slugify(event.name) or "no_name"
        folder_name = f"{timestamp}_{event.insta_post_id}"
        folder_path = os.path.join(base_dir, folder_name)

        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            print(f"❌ 폴더 생성 실패 ({folder_path}): {e}")
            return

        image_paths = []
        valid_image_urls = []  # ✅ webp 제거 후 다시 담을 리스트

        for idx, url in enumerate(event.image_url, start=1):
            try:
                if not url or not url.startswith("http"):
                    print(f"⚠️ 잘못된 URL → 스킵: {url}")
                    continue

                parsed = urlparse(url)
                ext = os.path.splitext(parsed.path)[1].lower().split("?")[0]

                # 🚫 webp 제외 — 아예 URL 리스트에서도 제거
                if ext == ".webp":
                    print(f"🚫 webp 파일 스킵 및 URL 제거: {url}")
                    continue

                if ext in ("", ".heic"):
                    ext = ".jpg"

                filename = f"{name_slug}_{idx}{ext}"
                filepath = os.path.join(folder_path, filename)

                resp = requests.get(url, timeout=20)
                if resp.status_code != 200:
                    print(f"⚠️ 다운로드 실패 (status={resp.status_code}): {url}")
                    continue

                content_type = resp.headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    print(f"⚠️ 이미지 아님 (Content-Type={content_type}): {url}")
                    continue

                with open(filepath, "wb") as f:
                    f.write(resp.content)

                image_paths.append(os.path.abspath(filepath))
                valid_image_urls.append(url)  # ✅ 실제로 성공한 URL만 유지
                print(f"✅ 이미지 저장 완료: {filepath}")

            except Exception as e:
                print(f"❌ 이미지 다운로드 처리 중 오류 ({url}): {e}")

        event.image_paths = image_paths
        event.image_url = valid_image_urls  # ✅ webp 제거 반영



    # ---------- 전체 파이프라인 ----------
    def process_file(self, filename, batch_size=10, download=False):
        posts = self.file_open(filename)
        sections = []
        section_to_post = {}
        for idx, post in enumerate(posts):
            if post.caption:
                sections.append((idx, post.caption))
                section_to_post[idx] = post

        if not sections:
            print("⚠️ 캡션 텍스트가 없습니다.")
            return []

        all_extracted: List[GptParsedEventDTO] = []
        for i in range(0, len(sections), batch_size):
            chunk = sections[i:i + batch_size]
            prompt = self.build_prompt(chunk)
            try:
                resp_text = self.call_gpt(prompt)
                # print("==== GPT RAW RESPONSE ====")
                # print(resp_text)
                extracted = self.extract_json_array(resp_text)
                all_extracted.extend(extracted)
            except Exception as e:
                print(f"⚠️ GPT 처리 실패: {e}")

        results = self._enrich_with_original(posts, all_extracted, section_to_post)

        if download:
            for event in results:
                self.download_images(event)

        # ✅ 필수 필드 필터링 추가
        before_len = len(results)
        results = self.filter_required_fields(results)
        after_len = len(results)
        print(f"📌 필수 필드 필터링: {before_len - after_len}건 제외됨")

        # 🧹 이미지 없는 팝업 제거
        before_len = len(results)
        results = [event for event in results if len(event.image_url) > 0 or len(event.image_paths) > 0]
        after_len = len(results)

        print(f"🧾 총 {before_len}건 중 {before_len - after_len}건은 이미지 없음으로 제외됨")

        return results


    # ---------- 실행 ----------
    @staticmethod
    def play(download=False):
        load_dotenv()
        token = os.getenv("GPT_ACCESS_TOKEN")
        if not token:
            print("❌ 환경 변수 누락: GPT_ACCESS_TOKEN")
            return
        api = GptAPI(token)
        results = api.process_file("popup.json", batch_size=10, download=download)
        api.file_save(results)
        print()


# ==============================
# 🏁 실행
# ==============================
if __name__ == "__main__":
    GptAPI.play(download=True)
