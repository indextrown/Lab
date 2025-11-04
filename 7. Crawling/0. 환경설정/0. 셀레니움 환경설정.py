from selenium import webdriver

# 크롬 드라이버 생성
driver = webdriver.Chrome()

# 원하는 페이지로 이동
driver.get("https://www.naver.com")

# 뒤로가기
driver.back()

# 앞으로 가기
driver.forward

# 새로고침
driver.refresh()

# 현재 URL 확인
print(driver.current_url)

# 페이지 제목 확인
driver.title

# 최대화
driver.maximize_window()

# 최소화
driver.minimize_window()

# 현재창 닫기
driver.close()

input()
# 모든 창을 닫고 웹드라이버 세션 종료
driver.quit()

# Chrome 브라우저를 오픈합니다
# driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
# driver.get("https://www.naver.com")