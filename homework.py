import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HOMEWORK_URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)

# настройка логгера
log_path = os.path.expanduser('~/ya_hw_bot.log')
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(log_path, maxBytes=2000000, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

START_MESSAGE = 'Запуск программы'
VERDICTS = {
    'rejected': 'У вас проверили работу "{homework}"!\n\n'
                'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа {homework} взята в ревью',
    'approved': 'У вас проверили работу "{homework}"!\n\n'
                'Ревьюеру всё понравилось, можно '
                'приступать к следующему уроку.',
}
UNEXPECTED_STATUS = (
    'При запросе "{homework}" бот столкнулся '
    'с неожиданным статусом: {status}'
)
ERROR_MESSAGE = (
    'При запросе данных бот столкнулся с ошибкой: "{error}".'
    '\nПараметры запроса:'
    '\n{url}'
    '\n{headers}'
    '\n{params}'
)
SERVER_REFUSAL_MESSAGE = (
    'Отказ от выполнения работы сервера. '
    'Причина отказа сервера: "{reason}"'
    '\nПараметры запроса:'
    '\n {url}'
    '\n {headers}'
    '\n{params}'
)
MESSAGE_SENT = 'Отправлено следующее сообщение: \n <{message}>\n'
BOT_ERROR_MESSAGE = 'Бот столкнулся с ошибкой: {error} \n'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(
            UNEXPECTED_STATUS.format(
                status=status, homework=homework_name))
    return VERDICTS[status].format(homework=homework_name)


def get_homework_statuses(current_timestamp):
    request_data = dict(url=HOMEWORK_URL, headers=HEADERS,
                        params={'from_date': current_timestamp})
    try:
        response = requests.get(**request_data)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            ERROR_MESSAGE.format(error=error, **request_data)
        )
    data = response.json()
    for key in ['code', 'error']:
        if key in data:
            raise RuntimeError(
                SERVER_REFUSAL_MESSAGE.format(
                    reason=data[key], **request_data))
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
                message = parse_homework_status(
                    new_homework.get("homeworks")[0])
                send_message(message, bot_client)
                logger.info(MESSAGE_SENT.format(message=message))
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)

            time.sleep(300)
        except Exception as error:
            logger.error(BOT_ERROR_MESSAGE.format(
                         error=error), exc_info=True)
            time.sleep(300)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='ya_hw_bot.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    )
    logging.getLogger('urlib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

    main()

    # # сбой сети
    # from unittest import TestCase, mock, main as uni_main # noqa
    # ReqEx = requests.RequestException

    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_raised(self, rq_get):
    #         rq_get.side_effect = mock.Mock(
    #             side_effect=ReqEx('testing'))
    #         main()
    # uni_main()

    # # отказ сервера
    # from unittest import TestCase, mock, main as uni_main
    # JSON = {'error': 'testing'}

    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_error(self, rq_get):
    #         resp = mock.Mock()
    #         resp.json = mock.Mock(
    #             return_value=JSON)
    #         rq_get.return_value = resp
    #         main()
    # uni_main()

    # # неожиданный статус
    # from unittest import TestCase, mock, main as uni_main
    # JSON = {'homeworks': [{'homework_name': 'test', 'status': 'test'}]}

    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_error(self, rq_get):
    #         resp = mock.Mock()
    #         resp.json = mock.Mock(
    #             return_value=JSON)
    #         rq_get.return_value = resp
    #         main()
    # uni_main()

    # # некорректный json
    # from unittest import TestCase, mock, main as uni_main
    # JSON = {'homeworks': 1}

    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_error(self, rq_get):
    #         resp = mock.Mock()
    #         resp.json = mock.Mock(
    #             return_value=JSON)
    #         rq_get.return_value = resp
    #         main()
    # uni_main()
