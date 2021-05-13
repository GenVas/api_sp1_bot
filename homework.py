import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
AUTHORIZATION_HEADER = f'OAuth {PRAKTIKUM_TOKEN}'
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HOMEWORK_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.DEBUG,
    filename='ya_hw_bot.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

# настройка логгера 1
log_path = os.path.expanduser('~/./ya_hw_bot.log')
logger = logging.getLogger(__name__)
logging.getLogger('urlib3').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
handler = RotatingFileHandler(log_path, maxBytes=2000000, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

HOMEWORK_STATUS = {
    'rejected': 'У вас проверили работу "{homework}"!\n\n'
                'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа {homework} взята в ревью',
    'approved': 'У вас проверили работу "{homework}"!\n\n'
                'Ревьюеру всё понравилось, можно '
                'приступать к следующему уроку.',
}
HOMEWORK_STATUS2 = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа {homework} взята в ревью',
    'approved': 'Ревьюеру всё понравилось, можно '
                'приступать к следующему уроку.',
}
ERROR_HW_STATUS = 'Ошибка статуса при запросе {homework}'
ERROR_MESSAGE = 'При запросе данных бот столкнулся с ошибкой:'
SERVER_ERROR_MESSAGE = 'Ошибка ответа сервера'
START_MESSAGE = 'Запуск программы'
KEY_NOT_FOUND_MESSAGE = 'Ключ не найден'
MESSAGE_SENT = 'Сообщение отправлено'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] not in HOMEWORK_STATUS.keys():
        raise ValueError(ERROR_HW_STATUS.format(homework=homework_name))
    for key, value in HOMEWORK_STATUS.items():
        if homework['status'] == key:
            status = value.format(homework=homework_name)
    return status


def get_homework_statuses(current_timestamp):
    json_error_codes = ['code', 'error']
    headers = {'Authorization': AUTHORIZATION_HEADER}
    # params = {'from_date': 0}  # параметр для отладки
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=HOMEWORK_URL,
            headers=headers,
            params=params
        )
    except Exception as error:
        exception_text = (f'{ERROR_MESSAGE} {error}')
        logger.error(f'{exception_text}', exc_info=True)
        bot_client.send_message(CHAT_ID, exception_text)
    else:
        data = response.json()
        for key in json_error_codes:
            if key in data:
                raise ValueError(SERVER_ERROR_MESSAGE)
        return data


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():
    logger.debug(START_MESSAGE)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get("homeworks"):
                send_message(parse_homework_status(
                    new_homework.get("homeworks")[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)
            raise KeyError(KEY_NOT_FOUND_MESSAGE)
        except Exception as error:
            logger.error(f'{error}', exc_info=True)
            try:
                bot_client.send_message(CHAT_ID, {error})
            except Exception as error:
                logger.debug(f'{error}', exc_info=True)
            time.sleep(300)
        else:
            logger.info(MESSAGE_SENT)


if __name__ == '__main__':
    main()
