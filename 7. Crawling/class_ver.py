from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psutil


# ✅ 프로세스 강제 종료
def shutdown(process_name: str = "chrome"):
    """남아있는 크롬 프로세스 정리"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in (proc.info['name'] or '').lower():
                print(f"Terminating {proc.info['name']} (PID {proc.info['pid']})")
                proc.terminate()
                proc.wait(timeout=3)
                print(f"✅ {proc.info['name']} 종료 완료")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


# ✅ 드라이버 설정 함수
def driver_Settings(headless: bool = False, exit: bool = True):
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

    # navigator.webdriver 감지 우회
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """}
    )

    return driver


# ✅ 컨텍스트 매니저 클래스
class Browser:
    def __init__(self, log: bool = True, **opts):
        self._driver = None
        self.opts = opts
        self.log = log

    # ------------------------
    # 내부 로그 처리 (_log)
    # ------------------------
    def __log(self, msg: str, color: str = None):
        """로그 출력 (color='green'|'red'|None)
        [Browser]는 고정된 bold white, msg만 색상 적용
        """
        if not self.log:
            return

        # ANSI 색상 코드
        colors = {
            "green": "\033[92m",   # 초록
            "red": "\033[91m",     # 빨강
            None: "\033[0m",       # 기본색
        }
        prefix_color = "\033[90m"   # [Browser] 부분 - 밝은 흰색(터미널 기본 강조)
        msg_color = colors.get(color, "\033[0m")
        reset = "\033[0m"

        print(f"{prefix_color}[Browser]{reset} {msg_color}{msg}{reset}")
    
    # ------------------------
    # 외부용 헬퍼 메서드
    # ------------------------
    def log_info(self, msg: str):
        """성공 / 진행 로그"""
        self.__log(msg, color="green")

    def log_error(self, msg: str):
        """오류 / 경고 로그"""
        self.__log(msg, color="red")

    def log_default(self, msg: str):
        """일반 로그"""
        self.__log(msg, color=None)

    def __enter__(self):
        self.log_info("🚀 driver 세팅 중...")
        self._driver = driver_Settings(**self.opts)
        # return self._driver # Selenium WebDriver 인스턴스
        return self # self를 반환(Brouser 인스턴스)

    def __exit__(self, exc_type, exc, tb):
        self.log_info("브라우저 종료 중...")  
        try:
            if self._driver:
                self._driver.quit()
                self.log_info("driver.quit() 완료")
        except Exception as e:
            self.log_error(f"⚠️ quit 실패: {e}")
        finally:
            shutdown()  # 남은 Chrome 프로세스 정리
            self._driver = None
            self.log_info("모든 프로세스 정리 완료")
    

    # ---- 기능 추가 ----
    def get(self, url: str):
        self.log_default("커스텀get")
        self._driver.get(url)

    def screenshot(self, filename: str = "screenshot.png"):
        """현재 페이지 스크린샷"""
        self._driver.save_screenshot(filename)
        self.log_default(f"📸 Screenshot saved to {filename}")
    
    def execute(self, script: str, *args):
        """JS 실행"""
        self.log_default(f"⚙️ Executing JS: {script[:60]}...")
        return self._driver.execute_script(script, *args)

    def find(self, by, value):
        """요소 찾기"""
        return self._driver.find_element(by, value)
    
    def click(self, by, value):
        """요소 클릭 (보이지 않아도 강제 클릭 시도)"""
        el = self.find(by, value)
        try:
            el.click()
        except Exception:
            self._driver.execute_script("arguments[0].click();", el)
        self.log_default(f"🖱️ Clicked element: {value}")

    def wait_for(self, by, value, timeout=10):
        """요소가 나타날 때까지 대기"""
        WebDriverWait(self._driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        self.log_default(f"✅ Element {value} appeared")

    def scroll_to_bottom(self):
        """스크롤 끝까지 내리기"""
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


# ✅ 사용 예시
if __name__ == "__main__":
    with Browser(headless=False, exit=False) as driver:
        driver.get("https://www.naver.com")
        driver.log_default("네이버 접속 완료")
        driver.screenshot("naver.png")
