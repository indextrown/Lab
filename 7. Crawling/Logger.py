# logger.py
import datetime

class Logger:
    COLORS = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "gray": "\033[90m",
        "reset": "\033[0m",
    }

    def __init__(self, prefix="[Browser]", enable=True):
        self.prefix = prefix
        self.enable = enable

    def _log(self, msg: str, color: str = None):
        if not self.enable:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix_color = self.COLORS["gray"]
        msg_color = self.COLORS.get(color, self.COLORS["reset"])
        reset = self.COLORS["reset"]
        print(f"{prefix_color}{self.prefix}{reset} [{ts}] {msg_color}{msg}{reset}")

    def info(self, msg: str):
        self._log(msg, "green")

    def warn(self, msg: str):
        self._log(msg, "yellow")

    def error(self, msg: str):
        self._log(msg, "red")

    def plain(self, msg: str):
        self._log(msg, None)
