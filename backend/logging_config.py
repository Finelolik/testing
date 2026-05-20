import logging
import logging.handlers
import sys
import os

# Папка для логов (создаётся автоматически)
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    """Настройка логирования: консоль + файл с ротацией."""
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Handler 1: консоль (stdout) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # --- Handler 2: файл с ротацией ---
    # maxBytes=5MB, backupCount=3 (хранит app.log, app.log.1, app.log.2, app.log.3)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # --- Основной логгер API ---
    api_logger = logging.getLogger("appeals_api")
    api_logger.setLevel(logging.INFO)

    # Убираем дублирующие handlers при повторном импорте
    if not api_logger.handlers:
        api_logger.addHandler(console_handler)
        api_logger.addHandler(file_handler)

    # --- Логгер безопасности (админы, удаление, входы) ---
    security_logger = logging.getLogger("appeals_api.security")
    security_logger.setLevel(logging.WARNING)

    # Отключаем дублирование логов от uvicorn access (опционально)
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []

    api_logger.info(f"Логирование настроено. Файл: {LOG_FILE}")

    return api_logger, security_logger