# logger_setup.py
import logging


def setup_logger():
    """Настройка логгера согласно заданию"""

    # Создание и настройка логгера
    logger = logging.getLogger('substation_rza')
    logger.setLevel(logging.DEBUG)

    # Обработчик для файла
    file_handler = logging.FileHandler('simulation.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Обработчик для консоли (только INFO и выше)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Добавление обработчиков
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Создаем глобальный экземпляр логгера для использования во всех модулях
logger = setup_logger()