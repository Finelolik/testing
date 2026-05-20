import logging
import sys

def setup_logging():
    """Настройка логирования для проекта."""
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler в stdout (для Docker/сервера)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Основной логгер API
    api_logger = logging.getLogger("appeals_api")
    api_logger.setLevel(logging.INFO)

    # Убираем дублирующие handlers при повторном импорте
    if not api_logger.handlers:
        api_logger.addHandler(console_handler)

    # Логгер безопасности (админы, удаление, входы)
    security_logger = logging.getLogger("appeals_api.security")
    security_logger.setLevel(logging.WARNING)

    # Отключаем дублирование логов от uvicorn access (опционально)
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []

    return api_logger, security_logger