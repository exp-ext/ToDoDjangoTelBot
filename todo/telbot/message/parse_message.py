import os
import re

import pytz
from dateparser.search import search_dates

from ..loader import bot

ADMIN_ID = os.getenv('ADMIN_ID')


class TaskParse:
    """
    Парсинг сообщения для работы с моделью Task.

    Принимает сообщение: str и часовой пояс: str.

    Имеет атрибуты:
    - message (:obj:`str`)
    - time_zone: (:obj:`str`)
    - server_date: (:obj:`datetime` with pytz | `None`)
    - user_date: (:obj:`datetime` with pytz | `None`)
    -period_repeat: str (default = N)
    -birthday: bool (default = False)

    Имеет методы:
    - `parse_with_parameters` - разбирает сообщение с параметрами,
    изменяя значения атрибутов класса.
    - `parse_without_parameters` - разбирает сообщение без параметров,
    изменяя значения атрибутов класса.
    - `it_birthday` (:obj:`bool`) - возвращает результат совпадения
    с birthday_list.
    - `get_parameters` (:obj:`str`) - разделяет строку, возвращает параметр
    повтора и убирает параметр из атрибута message.
    """
    BIRTHDAY_LIST = ['ДР', 'День Рождения', 'День рождения', 'день рождения',
                     'Birthday', 'birthday']
    PERIOD_DIC = {
        'день': 'D',
        'недел': 'W',
        'месяц': 'M',
        'год': 'Y',
    }

    def __init__(self, message: str, time_zone: str):
        self.message = message
        self.time_zone = time_zone
        self.server_date = None
        self.user_date = None
        self.only_message = ''
        self.period_repeat = 'N'
        self.birthday = any(
            word in message for word in TaskParse.BIRTHDAY_LIST
        )

    def _parse(self, message: str) -> None:
        """Дифференцирует текст определяя значения атрибутов класса."""
        pattern = r'(\d+)[\.](\d+)[\.]?'
        try:
            match = re.search(pattern, message)
            if match:
                date_ru = match.group()
                date_parser = date_ru.replace('.', '-')
                message = message.replace(date_ru, date_parser)

            settings = {
                'TIMEZONE': self.time_zone,
                'DATE_ORDER': 'DMY',
                'DEFAULT_LANGUAGES': ["ru"],
                'PREFER_DATES_FROM': 'future'
            }
            pars_tup = search_dates(
                message,
                add_detected_language=True,
                settings=settings
            )
            first_match = pars_tup[0] if pars_tup else None

            if isinstance(first_match, tuple):
                date = first_match[1]
                user_tz = pytz.timezone(self.time_zone)
                self.user_date = user_tz.localize(date)
                utc = pytz.utc

                if self.birthday:
                    self.server_date = utc.localize(
                        date.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                else:
                    self.server_date = self.user_date.astimezone(utc)

                message = message.replace(first_match[0], '').strip()
                self.only_message = (
                    message[:1].upper() + message[1:] if message else ''
                )

        except Exception as error:
            text = f'Не распарсил: {message}.\nОшибка: {error}'
            bot.send_message(chat_id=ADMIN_ID, text=text)

    def get_parameters(self) -> str:
        """Разделяет строку на сообщение и параметры"""
        message, *params = self.message.split('&')
        if params:
            for param in params:
                for key, value in TaskParse.PERIOD_DIC.items():
                    if key in param:
                        self.period_repeat = value
                        break
        return message

    def parse_with_parameters(self) -> None:
        """Распарсит сообщение с параметрами."""
        message = self.get_parameters()
        self._parse(message)

    def parse_without_parameters(self) -> None:
        """Распарсит сообщение без параметрами."""
        message = self.message
        self._parse(message)
