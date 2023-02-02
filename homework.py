import os
import sys

import logging
import time
import requests
from http import HTTPStatus

import telegram

from dotenv import load_dotenv

import exceptions

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

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
    """Проверка глобальный переменных."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if not all(tokens):
        logging.critical('Проблема с глобальными переменными.')
        sys.exit()


def get_api_answer(timestamp):
    """Отправка запроса к API."""
    params = {'from_date': timestamp}
    try:
        request = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if request.status_code == HTTPStatus.OK:
            response = request.json()
            return response
        elif request.status_code != HTTPStatus.OK:
            raise exceptions.APIStatusCodeError(
                f'Ошибка доступа к API, код ответа {request.status_code}')
    except requests.RequestException as error:
        return error


def check_response(response):
    """Расшифровка запроса."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Ошибка типа данных. Полученный тип: {type(response)}')
    if 'homeworks' not in response:
        raise exceptions.AbsentHomeworksInResponse(
            'Отсутсвует список homeworks.')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Ошибка типа данных. Полученный тип: {type(homeworks)}')
    last_homework = response['homeworks'][0]
    return last_homework


def parse_status(homework):
    """Определения статуса дз."""
    if 'homework_name' not in homework:
        raise exceptions.HWNameIsNull('Нет homework_name.')
    homework_name = homework['homework_name']
    hw_status = homework['status']
    if hw_status not in HOMEWORK_VERDICTS:
        raise exceptions.HWUnexpectedStatus('Неожиданный статус ДЗ.')
    verdict = HOMEWORK_VERDICTS[hw_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения ботом."""
    logging.debug('Попытка передачи сообщения в чат ТГ.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(f'Бот не смог отправить сообщение. Ошибка: {error}')
        return error
    else:
        logging.debug('Сообщение в чат ТГ отправлено.')


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    timestamp -= 30000000  # примерно минус месяц

    current_status = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            if len(response['homeworks']) == 0:
                timestamp = int(time.time())
                time.sleep(RETRY_PERIOD)
                continue
            homework = check_response(response)
            message = parse_status(homework)
            if message != current_status:
                current_status = message
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            break
        timestamp = int(time.time())
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
