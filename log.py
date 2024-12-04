import logging
from colorama import Fore, Style, init
init(autoreset=True)
def create_logger(__name__):

    # Настройка базового конфигуратора
    logging.basicConfig(
        level=logging.INFO,                   # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат вывода сообщений
        handlers=[
            logging.StreamHandler(),         # Вывод в консоль
            logging.FileHandler("app.log")   # Запись в файл "app.log"
        ]
    )

    return logging.getLogger(__name__)
