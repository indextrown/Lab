from Browser import Browser
from selenium.webdriver.common.by import By
import time

if __name__ == "__main__":
    id_value = ""
    pw_value = ""
    keyword_value = "아이폰"

    with Browser(headless=False, exit=True) as browser:
        browser.br_get("https://nid.naver.com/nidlogin.login?svctype=262144&url=http://m.naver.com/")
        browser.br_wait_for(By.NAME, "id")
        
        id = browser.br_find(By.CSS_SELECTOR, "#id")
        id.br_click()
        id.br_paste(id_value)
        
        pw = browser.br_find(By.CSS_SELECTOR, "#pw")
        pw.br_click()
        pw.br_paste(pw_value)

        login_btn = browser.br_find(By.CSS_SELECTOR, "#login_btn")
        login_btn.br_click()


        # 로직
        search_url = f"https://m.search.naver.com/search.naver?sm=mtb_hty.top&ssc=tab.m_blog.all&oquery=swift&tqi=iJmaXlprfAlssRPPZYRssssst1V-050144&query={keyword_value}&nso=so%3Add"
        browser.br_get(search_url)
        time.sleep(2)
        
        ids = browser.br_find_all(By.CSS_SELECTOR, ".name")
        print(ids)
        input()