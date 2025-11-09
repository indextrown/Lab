from dotenv import load_dotenv
import os
from Logger import Logger

# ✅ Mysql.py의 위치 기준으로 .env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from InstagramAPI import InstagramAPI
from GptAPI import GptAPI
from GeoCoding import GeoCoding
from Mysql import Mysql
from Alert import Alert

# 서버에서느 local = true로 해주세요(루프백 아이피이기 때문)
if __name__ == "__main__":
    InstagramAPI.play()         # 인스타그램 API 실행하여 팝업태그 게시글 반환 -> popup.json
    GptAPI.play(download=True)  # popup.json을 GPT로 정제 -> gpt.json
    GeoCoding.play()            # 도로명주소 및 좌표(경도/위도) 추가 -> popup_with_geo.json
    Mysql.play(local=False)     # mysql에 저장 -> mysql.json
    Alert.play(local=False)


# /Users/kimdonghyeon/.pyenv/versions/rest-venv/bin/python /Users/kimdonghyeon/2025/개발/SwiftLab/Lab/RestAPI/main.py
