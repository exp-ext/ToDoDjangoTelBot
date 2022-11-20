from datetime import datetime

import requests
from tasks.models import Task
from users.models import Group

from .loader import bot

LAST_TIME: int = 1


def main_process_distributor(cur_time_tup: int):
    """Основной модуль оповещающий о событиях в чатах."""
    # проверка на пропуск минут
    global LAST_TIME
    last_time_to_check = LAST_TIME

    if cur_time_tup - 60 > last_time_to_check:
        hour_start = datetime.fromtimestamp(
            last_time_to_check
        ).strftime('%H:%M')
        hour_end = datetime.fromtimestamp(
            cur_time_tup
        ).strftime('%H:%M')

        bot.send_message(
            225429268,
            f"пропуск времени с {hour_start} до {hour_end}"
        )
    LAST_TIME = cur_time_tup

    # поиск в базе событий для вывода в текущую минуту
    this_time = datetime.utcnow().replace(second=0, microsecond=0)

    tasks = Task.objects.filter(remind_at__startswith=this_time)


def send_forismatic_quotes() -> None:
    """Рассылка цитат великих людей на русском языке от АПИ forismatic."""
    try:
        response = requests.get(
            'http://api.forismatic.com/api/1.0/',
            {
                'method': 'getQuote',
                'format': 'text',
                'lang': 'ru',
            }
        )
    except Exception as error:
        raise KeyError(error)

    msg = '*Цитата на злобу дня:*\n' + response.text
    groups = Group.objects.all()

    for id in groups:
        bot.send_message(id.chat_id, msg, parse_mode='Markdown')
