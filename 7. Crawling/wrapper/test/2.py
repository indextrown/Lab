import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
from openpyxl import Workbook

# os.system('pip install --upgrade selenium')
# print(webdriver.__version__)


# 크롬 드라이버 자동 업데이트
chrome_options = Options()

# user agent
User_Agent =  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
chrome_options.add_argument(f'user-agent={User_Agent}')

chrome_options.add_argument("--headless")  # headless 모드 활성화
chrome_options.add_experimental_option("detach", True)

# 불필요한 에러 메시지 없애기
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# ChromeDriverManager를 통해 크롬 드라이버를 최신 버전으로 자동 설치하여 Service 생성 및 저장
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 웹페이지로 이동하고 웹페이지가 로딩될 때까지 최대 10초 대기
driver.implicitly_wait(10)

# 데이터를 저장할 빈 리스트
data = []

try:
    # open
    search = "맥북m1"
    keyword = ["m1", "16", "512"]
    min_money = 1000000
    max_money = 1300000
    page = 10

    cnt = 1
    while True:
        if cnt>page:
            break
        print(f"{cnt}페이지 입니다.")
        url = f"https://m.bunjang.co.kr/search/products?order=score&page={cnt}&q={search}"
        driver.get(url)
        li = driver.find_elements(By.CSS_SELECTOR, ".sc-dxZgTM.xRBLa")
        # time.sleep(3)
        for i in li:
            name = i.find_element(By.CSS_SELECTOR, "a>div:nth-child(2)>div").text
            price = int(i.find_element(By.CSS_SELECTOR, "a>div:nth-child(2)>div:nth-child(2)>div").text.replace(",", ""))
            url = i.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            if max_money >= price and min_money <=price:
                if all(key.lower() in name.lower() for key in keyword):
                    # print(f"제목: {name}\n가격: {price}\nURL: {url}\n")
                    data.append({"제목": name, "가격": price, "URL": url})
        cnt += 1

    # 브라우저 닫기
    driver.quit()
    # 데이터를 pandas DataFrame으로 변환
    df = pd.DataFrame(data)

    # DataFrame을 엑셀 파일로 저장
    excel_filename = 'products.xlsx'
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
        # 열 너비 설정
        for column_cells in writer.sheets['Sheet1'].columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            writer.sheets['Sheet1'].column_dimensions[column_cells[0].column_letter].width = length


        # openpyxl workbook 객체 얻기 및 세 번째 열의 너비 설정
        #workbook = writer.book
        #worksheet = writer.sheets['Sheet1']
        #worksheet.column_dimensions['C'].width = 50  # 'C' 열이 URL을 나타냄


    # df.to_excel(excel_filename, index=False)
    print(f"{excel_filename}에 저장되었습니다.")
    
except Exception as e:
    # 브라우저 닫기
    print("err: ", e)
    
    driver.quit()

