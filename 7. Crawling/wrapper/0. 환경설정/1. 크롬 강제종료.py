import psutil

def shutdown():
    # 종료하려는 프로세스 이름
    process_name = "chrome"  # 또는 "Google Chrome" (운영체제에 따라 다를 수 있음)

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

if __name__ == "__main__":
    shutdown()