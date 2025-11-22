import MyLib.CrawlingLib as CL

def main():
    try:
        driver = CL.driver_Settings(headless=False, exit=False)
        driver.get("https://www.naver.com")
    finally:
        driver.quit() 
        CL.shutdown()

if __name__ == "__main__":
    main()
