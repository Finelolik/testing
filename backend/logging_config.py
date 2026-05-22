import logging
import logging.handlers
import sys
import os

# mkdir
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    """Настройка логирования: консоль + файл с ротацией."""
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # файл с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # основной логгер
    api_logger = logging.getLogger("appeals_api")
    api_logger.setLevel(logging.INFO)

    # минус дубл handlers при повторном импорте
    if not api_logger.handlers:
        api_logger.addHandler(console_handler)
        api_logger.addHandler(file_handler)

    # логгер безопасности
    security_logger = logging.getLogger("appeals_api.security")
    security_logger.setLevel(logging.WARNING)

    # минус дубл логов от uviaccess
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []

    api_logger.info(f"Логирование настроено. Файл: {LOG_FILE}")

    return api_logger, security_logger