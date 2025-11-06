from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psutil
import time, random
# import pandas as pd
# import openpyxl
from selenium.webdriver.remote.webelement import WebElement
from Logger import Logger
import platform, sys, os
import pyperclip 
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException
import pyautogui

# ✅ 컨텍스트 매니저 클래스
class Browser:
    def __init__(self, log: bool = True, **opts):
        self._driver = None
        self.opts = opts
        self.log = Logger("[Browser]", enable=log)

        # 실행 환경 정보
        self.system_info = self.__get_system_info()
        self.br_log_info(f"🧠 실행 시스템: {self.system_info['os_name']} | "
                         f"{self.system_info['architecture']} | "
                         f"Python {self.system_info['python_version']}")
        
        # ✅ OS에 따라 단축키 지정
        self.ctrl_key = Keys.COMMAND if self.system_info["os_name"] == "Darwin" else Keys.CONTROL
    
    def __get_system_info(self) -> dict:
        """실행 중인 OS 및 시스템 정보를 반환"""
        return {
            "os_name": platform.system(),          # e.g., 'Darwin', 'Windows', 'Linux'
            "os_version": platform.version(),      # e.g., '23.5.0'
            "architecture": platform.machine(),    # e.g., 'arm64' or 'x86_64'
            "python_version": platform.python_version(),  # e.g., '3.11.7'
            "user": os.getenv("USER") or os.getenv("USERNAME", "Unknown")
        }

    def __enter__(self):
        self.br_log_info("🚀 driver 세팅 중...")
        self._driver = self.__driver_settings(**self.opts)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.br_log_info("브라우저 종료 중...")
        try:
            if self._driver:
                self._driver.quit()
                self.br_log_info("driver.quit() 완료")
        except Exception as e:
            self.br_log_error(f"⚠️ quit 실패: {e}")
        finally:
            self.__shutdown()
            self._driver = None
            self.br_log_info("모든 프로세스 정리 완료")
    
    
    # ------------------------
    # 내부 유틸 (함수 → 메서드화)
    # ------------------------
    def __shutdown(self, process_name: str = "chrome"):
        """남아있는 크롬 프로세스 정리"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in (proc.info['name'] or '').lower():
                    proc.terminate()
                    proc.wait(timeout=3)
                    self.br_log_info(f"✅ {proc.info['name']} 종료 완료")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    def __driver_settings(self, headless: bool = False, exit: bool = True):
        """Chrome 드라이버 설정 및 초기화"""
        options = Options()
        if not exit:
            options.add_experimental_option("detach", True)
        if headless:
            options.add_argument("--headless=new")

        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        options.add_argument('lang=ko_KR')
        options.add_argument('--window-size=932,932')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-automation')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        return driver
    
    # ------------------------
    # 외부용 헬퍼 메서드
    # ------------------------
    def br_log_info(self, msg: str): self.log.info(msg)
    def br_log_error(self, msg: str): self.log.error(msg)
    def br_log_default(self, msg: str): self.log.plain(msg)

    # ------------------------
    # Browser 전용 기능 메서드
    # ------------------------
    def br_get(self, url: str):
        self.br_log_default(f"br_get: {url}")
        self._driver.get(url)

    def br_screenshot(self, filename: str = "screenshot.png"):
        """현재 페이지 스크린샷"""
        self._driver.save_screenshot(filename)
        self.br_log_default(f"📸 Screenshot saved to {filename}")
    
    def br_execute(self, script: str, *args):
        """JS 실행"""
        self.br_log_default(f"⚙️ Executing JS: {script[:60]}...")
        return self._driver.execute_script(script, *args)

    def br_wait_for(self, by, value, timeout=10):
        """요소가 나타날 때까지 대기"""
        WebDriverWait(self._driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        self.br_log_default(f"br_wait_for: Element {value} appeared")

    def br_scroll_to_bottom(self):
        """스크롤 끝까지 내리기"""
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def br_find(self, by, value):
        """전체 페이지에서 요소 1개 탐색 (Browser 기준)"""
        try:
            el = self._driver.find_element(by, value)
            # self.br_log_default(f"🔍 Found element: {value}")
            return BrElement(el, self)
        except Exception as e:
            self.br_log_error(f"❌ 요소 탐색 실패: {value} ({e})")
            return None

    def br_find_all(self, by, value):
        """전체 페이지에서 요소 여러 개 탐색 (Browser 기준)"""
        try:
            els = self._driver.find_elements(by, value)
            self.br_log_default(f"🔎 Found {len(els)} elements: {value}")
            return [BrElement(e, self) for e in els]
        except Exception as e:
            self.br_log_error(f"❌ 여러 요소 탐색 실패: {value} ({e})")
            return []


# ------------------------
# WebElement 확장 클래스
# ------------------------
class BrElement:
    def __init__(self, element: WebElement, driver):
        self._el = element
        self._driver = driver  # Browser 참조용

    def br_find(self, by, value):
        try:
            el = self._el.find_element(by, value)
            # self._driver.br_log_default(f"🔍 Found element: {value}")
            return BrElement(el, self._driver)
        except Exception as e:
            self._driver.br_log_error(f"❌ 요소 탐색 실패: {value} ({e})")
            return None

    def br_find_all(self, by, value):
        try:
            els = self._el.find_elements(by, value)
            self._driver.br_log_default(f"🔎 Found {len(els)} elements: {value}")
            return [BrElement(e, self._driver) for e in els]
        except Exception as e:
            self._driver.br_log_error(f"❌ 여러 요소 탐색 실패: {value} ({e})")
            return []

    def get_attribute(self, name):
        return self._el.get_attribute(name)
    
    def br_click(self):
        try:
            self._el.click()
            # self._driver.br_log_default("🖱️ Clicked element")
        except Exception:
            self._driver._driver.execute_script("arguments[0].click();", self._el)
            self._driver.br_log_default("🖱️ Clicked element (via JS)")

    # 구글 뉴스 같은 크롤링에선 줄바꿈 문자나 공백이 섞이기 쉬워서 아래처럼 다듬는 게 좋아요:
    @property
    def text(self):
        # return self._el.text
        return self._el.text.strip().replace("\n", " ")
    
    # 원문이 필요할 때
    def raw_text(self):
        """원본 줄바꿈 포함 텍스트"""
        return self._el.text
    
    # ------------------------
    # 📋 복사 / 붙여넣기 메서드
    # ------------------------
    def br_copy(self):
        """요소의 value/text를 클립보드에 복사"""
        try:
            value = self._el.get_attribute("value") or self._el.text
            value = value.strip()
            pyperclip.copy(value)
            self._driver.br_log_default(f"📋 복사 완료: '{value[:40]}...'")
            return value
        except Exception as e:
            self._driver.br_log_error(f"❌ 복사 실패: {e}")
            return None

    def br_paste(self, text: str, min_delay=0.05, max_delay=0.15):
        """pyperclip + pyautogui.hold 방식으로 자연스러운 붙여넣기"""
        try:
            pyperclip.copy(text)
            self._el.click()
            time.sleep(0.5)
            key = "command" if platform.system() == "Darwin" else "ctrl"
            with pyautogui.hold([key]):
                pyautogui.press("v")
            time.sleep(0.5)
            # self._driver.br_log_default("📎 붙여넣기 완료")
        except Exception as e:
            self._driver.br_log_error(f"❌ 붙여넣기 실패: {e}")



# ✅ 사용 예시
# 초록색 로그: 시스템 제어 
# 일반색 로그: 기능 실행
if __name__ == "__main__":
    with Browser(headless=False, exit=False) as driver:
        driver.br_get("https://www.naver.com")
        driver.br_log_default("네이버 접속 완료")
        driver.br_screenshot("naver.png")






















# if __name__ == "__main__":
#     search = "아이폰"
#     page_nums = 5
#     data = []

#     with Browser(headless=False, exit=False) as driver:
#         driver.br_log_default(f"🔍 구글 뉴스 검색 시작: {search}")

#         for page_num in range(0, page_nums * 10, 10):
#             url = f"https://www.google.com/search?q={search}&tbm=nws&start={page_num}"
#             driver.br_get(url)
#             time.sleep(2)

#             driver.br_wait_for(By.CSS_SELECTOR, "#rso > div > div > div", timeout=5)
#             posts = driver.br_find_all(By.CSS_SELECTOR, "#rso > div > div > div")

#             for post in posts:
#                 try:
#                     post_info = post.br_find_all(
#                         By.CSS_SELECTOR, "div > div > a > div > div:nth-child(2) > div"
#                     )
#                     company = post_info[0].text if len(post_info) > 0 else ""
#                     title = post_info[1].text if len(post_info) > 1 else ""
#                     content = post_info[2].text if len(post_info) > 2 else ""
#                     time_text = post_info[-1].text if post_info else ""
#                     post_url = post.br_find(
#                         By.CSS_SELECTOR, "div > div > a"
#                     ).get_attribute("href")

#                     data.append([company, title, content, time_text, post_url])

#                 except Exception as e:
#                     driver.br_log_error(f"❌ 게시물 파싱 중 오류: {e}")

#             driver.br_log_info(f"✅ {page_num // 10 + 1}페이지 완료 ({len(posts)}건 수집)")

#         df = pd.DataFrame(data, columns=["Company", "Title", "Content", "Time", "Link"])
#         driver.br_log_default(f"📊 총 {len(df)}건 뉴스 수집 완료")

#         df.to_excel(f"{search}_news_results.xlsx", index=False)
#         driver.br_log_default(f"💾 {search}_news_results.xlsx 파일 저장 완료")
