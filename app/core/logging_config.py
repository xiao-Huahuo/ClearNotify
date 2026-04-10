import logging
from logging.handlers import RotatingFileHandler

from app.core.config import GlobalConfig


class SafeRotatingFileHandler(RotatingFileHandler):
    def doRollover(self) -> None:
        try:
            super().doRollover()
        except PermissionError:
            self._reopen_current_stream()
        except OSError as exc:
            if getattr(exc, "winerror", None) == 32:
                self._reopen_current_stream()
                return
            raise

    def _reopen_current_stream(self) -> None:
        try:
            if self.stream:
                try:
                    self.stream.flush()
                finally:
                    self.stream.close()
        except Exception:
            pass

        self.stream = None
        if not self.delay:
            self.stream = self._open()


def setup_logging() -> None:
    GlobalConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = SafeRotatingFileHandler(
        GlobalConfig.APP_LOG_PATH,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    existing_file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == str(GlobalConfig.APP_LOG_PATH)
    ]
    if existing_file_handlers:
        return

    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
