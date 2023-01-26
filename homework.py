import os
import sys

import time
import requests

import telegram

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('YATOKEN')
TELEGRAM_TOKEN = os.getenv('TGTOKEN')
TELEGRAM_CHAT_ID = os.getenv('TGCHATID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if PRACTICUM_TOKEN is None:
        print('PRACTICUM_TOKEN is Null.')
        sys.exit()
    if TELEGRAM_TOKEN is None:
        print('TELEGRAM_TOKEN is Null.')
        sys.exit()
    if TELEGRAM_CHAT_ID is None:
        print('TELEGRAM_CHAT_ID is Null.')
        sys.exit()


def get_api_answer(timestamp):
    params = {'from_date': timestamp}
    ping = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if ping.status_code == 200:
        response = ping.json()
        return response


def check_response(response):
    last_homework = response['homeworks'][0]
    return last_homework


def parse_status(homework):
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def main():
    """Основная логика работы бота."""

    check_tokens()

    # bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0

    response = get_api_answer(timestamp)
    homework = check_response(response)
    message = parse_status(homework)
    # send_message(bot, message)
    print(message)


if __name__ == '__main__':
    main()
