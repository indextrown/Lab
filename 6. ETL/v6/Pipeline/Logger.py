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
    
    def __init__(self, prefix: str = "", enable: bool = True, stream=None, use_color: bool = True):
        """
        Args:
            prefix (str): 로그 앞 태그
            enable (bool): 로그 출력 여부
            stream: 출력 대상
            use_color (bool): ANSI 컬러 사용 여부
        """
        self.prefix = f"[{prefix}]" if prefix else ""
        self.enable = enable
        self.stream = stream or sys.stdout
        self.use_color = use_color

    def _color(self, code: str):
        """ use_color=False 이면 색상 코드 제거 """
        if not self.use_color:
            return ""
        return self.COLORS[code]

    def _log(self, msg: str, color: str = None):
        if not self.enable:
            return

        ts = datetime.datetime.now().strftime("%H:%M:%S")

        prefix_color = self._color("gray")
        msg_color = self._color(color) if color else ""
        reset = self._color("reset")

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
    log1 = Logger("Browser", use_color=True)   # 컬러 ON
    log2 = Logger("DB", use_color=False)       # 컬러 OFF
    log3 = Logger("Crawler", use_color=True)

    log1.info("드라이버 실행 완료")
    log2.warn("컬러 없음")
    log3.error("요청 실패")
