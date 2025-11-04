from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# 데이터 출력
import pandas as pds

# 프로세스 관리
import psutil

# 프로세스 강제종료
def shutdown(process_name: str = "chrome"):
    # 종료하려는 프로세스 이름
    # 또는 "Google Chrome" (운영체제에 따라 다를 수 있음)

    # 모든 프로세스를 조회하여 이름이 'chrome'인 프로세스를 종료
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 프로세스 이름이 chrome인지 확인
            if process_name.lower() in proc.info['name'].lower():
                print(f"Terminating process {proc.info['name']} with PID {proc.info['pid']}")
                proc.terminate()  # 프로세스 종료
                proc.wait()  # 종료가 완료될 때까지 대기
                print(f"Process {proc.info['name']} terminated successfully")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # 프로세스가 이미 종료되었거나 권한이 없을 경우 예외 처리

## 드라이버 최적화
def driver_Settings(headless: bool, exit: bool):
    options = Options()

    # 웹드라이버 종료 안시키고 유지
    if not exit:
        options.add_experimental_option("detach", True)

    # 주석해제하면 헤드리스 모드
    if headless:
        options.add_argument("--headless=new")  # 헤드리스 모드로 실행

    # Windows 10 운영 체제에서 Chrome 브라우저를 사용하는 것처럼 보이는 사용자 에이전트가 설정
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 언어 설정을 한국어로 지정. 이는 웹 페이지가 한국어로 표시
    options.add_argument('lang=ko_KR')

    # 브라우저 창의 크기를 지정. 여기서는 너비 932px, 높이 932px로 설정
    options.add_argument('--window-size=932,932')

    # GPU 가속을 비활성화. GPU 가속이 활성화되어 있으면, Chrome이 GPU를 사용하여 그래픽을 렌더링하려고 시도할 수 있기때문. 일부 환경에서는 GPU 가속이 문제를 일으킬 수 있으므로 이 옵션을 사용하여 비활성화
    options.add_argument('--disable-gpu')

    # 정보 표시줄을 비활성화. 정보 표시줄은 Chrome 브라우저 상단에 나타나는 알림이나 메시지를 의미. 이 옵션을 사용하여 이러한 알림이 나타나지 않도록 설정.
    options.add_argument('--disable-infobars')

    # 확장 프로그램을 비활성화. Chrome에서 확장 프로그램을 사용하지 않도록 설정
    options.add_argument('--disable-extensions')

    #  자동화된 기능을 비활성화. 이 옵션은 Chrome이 자동화된 환경에서 실행되는 것을 감지하는 것을 방지
    options.add_argument('--disable-blink-features=AutomationControlled')

    # 자동화를 비활성화. 이 옵션은 Chrome이 자동화 도구에 의해 제어되는 것으로 감지되는 것을 방지
    options.add_argument('--disable-automation')

    # 서버/컨테이너 환경에서 크롬이 안 뜨는 문제를 줄이기 위해 샌드박스 기능을 끄는 옵션
    options.add_argument("--no-sandbox")  # 샌드박스 모드 비활성화 (리눅스 환경용)

    # 컨테이너/서버에서 크롬이 메모리 부족으로 뻗는 문제를 줄여주는 옵션
    options.add_argument("--disable-dev-shm-usage")  # /dev/shm (공유)메모리 사용 방지 (Docker, AWS 환경에서 유용)

    # 사이트에서 ‘Selenium으로 제어 중’인 것을 들키지 않도록 하는 첫 번째 단계
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Selenium이 여는 크롬에서 자동화 전용 확장을 꺼서 탐지 가능성을 낮추는 옵션
    options.add_experimental_option('useAutomationExtension', False)


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # navigator.webdriver 감지 우회: 새 탭/문서가 로드될 때마다 먼저 실행되는 스크립트로 등록
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
        }
    )


    return driver

if __name__ == "__main__":
    try:
        driver = driver_Settings(headless=False, exit=False)
        driver.get("https://www.naver.com")
    finally:
        driver.quit()
        shutdown()




# # ✅ 프로세스 강제 종료
# def shutdown(process_name: str = "chrome"):
#     """남아있는 크롬 프로세스 정리"""
#     for proc in psutil.process_iter(['pid', 'name']):
#         try:
#             if process_name.lower() in (proc.info['name'] or '').lower():
#                 print(f"Terminating {proc.info['name']} (PID {proc.info['pid']})")
#                 proc.terminate()
#                 proc.wait(timeout=3)
#                 print(f"✅ {proc.info['name']} 종료 완료")
#         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#             pass


# # ✅ 드라이버 설정 함수
# def driver_Settings(headless: bool = False, exit: bool = True):
#     options = Options()

#     if not exit:
#         options.add_experimental_option("detach", True)

#     if headless:
#         options.add_argument("--headless=new")

#     options.add_argument(
#         'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
#         'AppleWebKit/537.36 (KHTML, like Gecko) '
#         'Chrome/120.0.0.0 Safari/537.36'
#     )
#     options.add_argument('lang=ko_KR')
#     options.add_argument('--window-size=932,932')
#     options.add_argument('--disable-gpu')
#     options.add_argument('--disable-infobars')
#     options.add_argument('--disable-extensions')
#     options.add_argument('--disable-blink-features=AutomationControlled')
#     options.add_argument('--disable-automation')
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#     # navigator.webdriver 감지 우회
#     driver.execute_cdp_cmd(
#         "Page.addScriptToEvaluateOnNewDocument",
#         {"source": """
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined
#             })
#         """}
#     )

#     return driver

