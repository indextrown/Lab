from Browser import Browser
from selenium.webdriver.common.by import By
import time
from Logger import Logger


def search(browser, text, keyword, min_money, max_money, page):
    data = []
    cnt = 1
    while True:
        if cnt > page: break

        browser.br_log_info(f"{cnt} 페이지")
        url = f"https://m.bunjang.co.kr/search/products?order=score&page={cnt}&q={searchText}"
        browser.br_get(url)
        time.sleep(2)

        # ✅ 상위(wrapper) 1개 찾기
        wrapper = browser.br_find(By.CSS_SELECTOR, ".sc-fyjhYU.fXWErr")

        # ✅ 하위 리스트(상품들) 전부 찾기(“링크(a) 중에서, href 속성에 ‘/products/’가 들어있는 요소”를 모두 찾는다.)
        products = wrapper.br_find_all(By.CSS_SELECTOR, "a[href*='/products/']") 
        for product in products:
            name = product.br_find(By.CSS_SELECTOR, "a > div:nth-child(2) > div").text
            price = product.br_find(By.CSS_SELECTOR, "a > div:nth-child(2) > div:nth-child(2) > div").text
            url = product.get_attribute("href")

            browser.br_log_default(name)
            print(price)
            print(url)
            
            
            pass
        cnt += 1

with Browser(headless=False, exit=True) as browser:
    searchText = "맥북m1"
    keyword = ["m1", "16"]
    min_money = 1000000
    max_money = 1300000
    page = 3
    search(browser, searchText, keyword, min_money, max_money, page)

    # 쉬는법
    # browser.br_execute("""
    #         return document.readyState === 'complete';
    #     """)