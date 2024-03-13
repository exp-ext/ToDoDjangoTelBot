import asyncio
import os
import re
from datetime import datetime

import pytz
from dateparser.search import search_dates

from ..loader import bot

ADMIN_ID = os.getenv('ADMIN_ID')
DATE_PATTERN = re.compile(r'(\d+)[\.](\d+)[\.]?')
DIGITS_PATTERN = re.compile(r'\d+')


class TaskParse:
    """
    Парсинг сообщения для работы с моделью Task.

    Принимает сообщение: str и часовой пояс: str.

    Имеет атрибуты:
    - message (:obj:`str`)
    - time_zone: (:obj:`str`)
    - server_date: (:obj:`datetime` with pytz | `None`)
    - user_date: (:obj:`datetime` with pytz | `None`)
    - period_repeat: str (default = N)
    - birthday: bool (default = False)
    - get_parameters(): получает параметры в сообщении

    Имеет методы:
    - `it_birthday` (:obj:`bool`) - возвращает результат совпадения
    с birthday_list.
    - `parse_message` (:obj:`str`) - разделяет строку, вызывая методы
    и заполняя атрибуты.
    """
    BIRTHDAY_LIST = ['ДР', 'День Рождения', 'День рождения', 'день рождения',
                     'Birthday', 'birthday']
    PERIOD_DIC = {
        'разовое': 'N',
        'день': 'D',
        'недел': 'W',
        'месяц': 'M',
        'год': 'Y',
    }

    def __init__(self, inbox_message: str, time_zone: str):
        self.inbox_message = inbox_message
        self.time_zone = time_zone
        self.server_date = None
        self.user_date = None
        self.delta_time_min = None
        self.only_message = ''
        self.period_repeat = 'N'
        self.utc = pytz.utc
        self.birthday = any(word in inbox_message for word in self.BIRTHDAY_LIST)

    async def parse_message(self) -> None:
        """Дифференцирует текст определяя значения атрибутов класса."""
        await asyncio.gather(
            self.get_period_repeat(),
            self.get_delta_time_min()
        )
        initial_message = self.inbox_message
        try:
            match = DATE_PATTERN.search(initial_message)
            if match:
                date_ru = match.group()
                date_parser = date_ru.replace('.', '-')
                initial_message = initial_message.replace(date_ru, date_parser)

            settings = {
                'TIMEZONE': self.time_zone,
                'DATE_ORDER': 'DMY',
                'DEFAULT_LANGUAGES': ["ru"],
                'PREFER_DATES_FROM': 'future'
            }
            pars_tup = search_dates(
                initial_message,
                add_detected_language=True,
                settings=settings
            )
            first_match = pars_tup[0] if pars_tup else None

            if isinstance(first_match, tuple):
                date = first_match[1]
                string_date = first_match[0]

                await asyncio.gather(
                    self.set_user_server_date(date),
                    self.set_only_message(initial_message, string_date)
                )

        except Exception as error:
            text = f'Не распарсил: {initial_message}.\nОшибка: {error}'
            bot.send_message(chat_id=ADMIN_ID, text=text)

    async def set_only_message(self, initial_message: str, string_date: str):
        """Удаляет дату из текста сообщения и назначает его only_message."""
        message = initial_message.replace(string_date, '').strip()
        self.only_message = message[:1].upper() + message[1:] if message else ''

    async def set_user_server_date(self, date: datetime):
        """Назначает datetime user_date относительно его ТЗ и datetime server_date по UTC."""
        user_tz = pytz.timezone(self.time_zone)
        self.user_date = user_tz.localize(date)
        if self.birthday:
            self.server_date = self.utc.localize(date.replace(hour=0, minute=0, second=0, microsecond=0))
        else:
            self.server_date = self.user_date.astimezone(self.utc)

    async def get_period_repeat(self) -> str:
        """
        Разделяет строку на сообщение и параметры и назначаем
        соответствующие атрибуты, если параметры получены.
        """
        _, *params = self.inbox_message.split('&')
        for param in params:
            for key, value in self.PERIOD_DIC.items():
                if key in param:
                    self.period_repeat = value
                    break

    async def get_delta_time_min(self) -> str:
        """
        Разделяет строку на сообщение и параметры и назначает
        соответствующие атрибуты, если параметры получены.
        """
        message, params = self.inbox_message.split('|')
        if params:
            numbers = DIGITS_PATTERN.findall(params)
            self.inbox_message = message.strip()
            self.delta_time_min = int(numbers[0])
