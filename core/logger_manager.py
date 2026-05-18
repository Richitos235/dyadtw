import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    import colorlog
except ImportError:  # pragma: no cover
    colorlog = None


class LoggerManager:
    def __init__(self, file_path: Path, level: str = "INFO") -> None:
        self.file_path = file_path
        self.logger = logging.getLogger("westbot")
        self.logger.setLevel(self.resolve_level(level))
        self.logger.propagate = False
        self.configure_handlers()

    @staticmethod
    def resolve_level(level: str) -> int:
        return getattr(logging, level.upper(), logging.INFO)

    def configure_handlers(self) -> None:
        self.logger.handlers.clear()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        console_handler = logging.StreamHandler()
        if colorlog is not None:
            formatter = colorlog.ColoredFormatter(
                "%(.cyan)s%(asctime)s%(reset)s %(log_color)s[%(levelname)s]%(reset)s %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        else:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        rotating_handler = RotatingFileHandler(self.file_path, maxBytes=5_242_880, backupCount=5, encoding="utf-8")
        rotating_handler.setFormatter(file_formatter)
        self.logger.addHandler(rotating_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
