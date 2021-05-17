import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}/'}
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HOMEWORK_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)

# настройка логгера
log_path = os.path.expanduser('~/ya_hw_bot.log')
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(log_path, maxBytes=2000000, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

START_MESSAGE = 'Запуск программы'
STATUS_MESSAGE_DICT = {
    'rejected': 'У вас проверили работу "{homework}"!\n\n'
                'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа {homework} взята в ревью',
    'approved': 'У вас проверили работу "{homework}"!\n\n'
                'Ревьюеру всё понравилось, можно '
                'приступать к следующему уроку.',
}
ERROR_STATUS = 'При запросе {homework} ошибка статуса: {status}'
ERROR_MESSAGE = ('При запросе данных бот столкнулся с ошибкой: '
                 '{error}.'
                 '\n.Параметры запроса:')
SERVER_REFUSAL_MESSAGE = ('Отказ от выполнения работы сервера. '
                          'Вернулся ключ "{key}".'
                          '\nПараметры запроса:')
MESSAGE_SENT = 'Сообщение отправлено'
ERROR_SENT_TO_BOT_MESSAGE = ('При отправке сообшения в Телеграм бот '
                             'столкнулся с ошибкой {error}')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in STATUS_MESSAGE_DICT:
        raise ValueError(
            f'{ERROR_STATUS.format(status=status)}')
    return STATUS_MESSAGE_DICT[status].format(homework=homework_name)


def get_homework_statuses(current_timestamp):
    # params = {'from_date': 0}  # параметр для отладки
    params = {'from_date': current_timestamp}
    request_data = dict(url=HOMEWORK_URL, headers=HEADERS, params=params)
    try:
        response = requests.get(**request_data)
        data = response.json()
        for key in ['code', 'error']:
            if key in data:
                raise ValueError(
                    f'{SERVER_REFUSAL_MESSAGE.format(key=key)}'
                    f'{request_data}')
        return data
    except requests.exceptions.RequestException as error:
        logger.error(
            f'{ERROR_MESSAGE.format(error=error)}'
            f'{request_data}')


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():

    logging.basicConfig(
        level=logging.DEBUG,
        filename='ya_hw_bot.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    )
    logging.getLogger('urlib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

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
            logger.info(MESSAGE_SENT)
            time.sleep(300)
        except Exception as error:
            logger.error(ERROR_SENT_TO_BOT_MESSAGE.format(
                         error={error}), exc_info=True)
            time.sleep(300)


if __name__ == '__main__':
    main()
