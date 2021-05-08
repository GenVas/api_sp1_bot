import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
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
logger = logging.getLogger()
logging.getLogger('urlib3').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
handler = RotatingFileHandler('ya_hw_bot.log', maxBytes=2000000, backupCount=5)
logger.addHandler(handler)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, можно '
                   'приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    # params = {'from_date': 0}  # параметр для отладки
    params = {'from_date': current_timestamp}
    response = requests.get(
        url=HOMEWORK_URL,
        headers=headers,
        params=params)
    try:
        response.raise_for_status()
    except Exception as e:
        exception_message = f'При запросе данных бот столкнулся с ошибкой: {e}'
        logger.error(f'{e}')
        logger.error(f'{exception_message}')
        bot_client.send_message(CHAT_ID, exception_message)
    else:
        return response.json()
    return response.json()


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():
    logger.debug('Запуск программы')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get("homeworks"):
                send_message(parse_homework_status(
                    new_homework.get("homeworks")[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(30)

        except Exception as e:
            exception_message = f'Бот столкнулся с ошибкой: {e}'
            logger.error(f'{exception_message}')
            bot_client.send_message(CHAT_ID, exception_message)
            time.sleep(60)
        else:
            logger.info('Сообщение отправлено')


if __name__ == '__main__':
    main()
