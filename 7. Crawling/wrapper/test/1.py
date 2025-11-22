from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 크롬 드라이버 자동 업데이트
chrome_options = Options()
chrome_options.add_argument("--headless")  # headless 모드 활성화
chrome_options.add_experimental_option("detach", True)

# 불필요한 에러 메시지 없애기
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# ChromeDriverManager를 통해 크롬 드라이버를 최신 버전으로 자동 설치하여 Service 생성 및 저장
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 웹페이지로 이동하고 웹페이지가 로딩될 때까지 최대 10초 대기
driver.implicitly_wait(10)

search = "맥북 프로 M1"
min_money = 1000000
max_money = 1300000
page = 5


cnt = 1
while True:
    if cnt > page:
        break
    # 웹 페이지 열기
    print(f"{cnt}페이지 입니다.")
    driver.get(f"https://m.bunjang.co.kr/search/products?order=score&page={cnt}&q={search}")
    # CSS 선택자를 사용하여 제품 목록 찾기
    li = driver.find_elements(By.CSS_SELECTOR, ".sc-eTpRJs.ekyrKV")

    for i in li:
        # 이름과 가격을 찾아서 출력
        urls = i.find_elements(By.CSS_SELECTOR, ".sc-dxZgTM.xRBLa>a")
        names = i.find_elements(By.CSS_SELECTOR, ".sc-iBEsjs.fqRSdX")
        prices = i.find_elements(By.CSS_SELECTOR, ".sc-kxynE.fnToiW>div.sc-hzNEM.bmEaky")
        
        for url, name, price in zip(urls, names, prices):
            price_text = int(price.text.replace(",", ""))
            if max_money >= price_text and min_money <=price_text:
                print(f"제목: {name.text}\n가격: {price_text}\nURL: {url.get_attribute('href')}\n")
    cnt+=1

# 브라우저 닫기
driver.quit()
