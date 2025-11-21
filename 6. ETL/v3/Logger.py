import datetime
import sys

class Logger:
    COLORS = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "gray": "\033[90m",
        "reset": "\033[0m",
    }

    def __init__(self, prefix: str = "", enable: bool = True, stream=None):
        """
        Args:
            prefix (str): 로그 앞에 붙는 태그 (예: [Browser], [DB], [API])
            enable (bool): False면 로그 비활성화
            stream: 출력 대상 (기본은 sys.stdout)
        """
        self.prefix = f"[{prefix}]" if prefix else ""
        self.enable = enable
        self.stream = stream or sys.stdout

    def _log(self, msg: str, color: str = None):
        if not self.enable:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix_color = self.COLORS["gray"]
        msg_color = self.COLORS.get(color, self.COLORS["reset"])
        reset = self.COLORS["reset"]
        formatted = f"{prefix_color}{self.prefix}{reset} [{ts}] {msg_color}{msg}{reset}\n"
        self.stream.write(formatted)
        self.stream.flush()

    def info(self, msg: str):
        self._log(msg, "green")

    def warn(self, msg: str):
        self._log(msg, "yellow")

    def error(self, msg: str):
        self._log(msg, "red")

    def plain(self, msg: str):
        self._log(msg, None)

if __name__ == "__main__":
    log1 = Logger("Browser")
    log2 = Logger("DB")
    log3 = Logger("Crawler", enable=True)

    log1.info("드라이버 실행 완료")
    log2.warn("커넥션이 느립니다")
    log3.error("요청 실패")
    log3.plain("테스트 메시지")