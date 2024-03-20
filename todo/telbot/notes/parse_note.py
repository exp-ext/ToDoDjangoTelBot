import asyncio
import os
import traceback
from datetime import datetime

import pytz
from ai.gpt_exception import handle_exceptions
from core.re_compile import DATE_PATTERN
from dateparser.search import search_dates
from django.db.models import Model
from telbot.gpt.reminder_gpt import ReminderGPT

ADMIN_ID = os.getenv('ADMIN_ID')


class TaskParse:
    """
    Парсинг сообщения для работы с моделью Task.

    ### Args:
    - inbox_message (`str`): Входное сообщение для парсинга.
    - time_zone (`str`): Часовой пояс пользователя.
    - user (`Model`): Объект пользователя.
    - chat_id (`int`): Идентификатор чата.
    - only_datetime_and_message (`bool`, optional): Флаг для определения, нужно ли парсить только дату и сообщение.

    """

    PERIOD_DIC = ['N', 'D', 'W', 'M', 'Y']

    def __init__(self, inbox_message: str, time_zone: str, user: Model, chat_id: int, only_datetime_and_message: bool = False):
        """
        Инициализация объекта TaskParse.

        """
        self.inbox_message = inbox_message
        self.time_zone = time_zone
        self.server_datetime = None
        self.user_datetime = None
        self.delta_time_min = None
        self.only_message = ''
        self.period_repeat = 'N'
        self.utc = pytz.utc
        self.user = user
        self.chat_id = chat_id
        self.only_datetime_and_message = only_datetime_and_message

    async def parse_message(self) -> None:
        """
        Дифференцирует текст определяя значения атрибутов класса.

        ### Raises:
        - ValueError: Если возникает ошибка при получении даты.

        """
        try:
            match = DATE_PATTERN.search(self.inbox_message)
            if match:
                date_ru = match.group()
                date_parser = date_ru.replace('.', '-')
                self.inbox_message = self.inbox_message.replace(date_ru, date_parser)

            settings = {
                'TIMEZONE': self.time_zone,
                'DATE_ORDER': 'DMY',
                'DEFAULT_LANGUAGES': ['ru'],
                'PREFER_DATES_FROM': 'future'
            }
            pars_tup = search_dates(
                self.inbox_message,
                add_detected_language=True,
                settings=settings
            )
            if pars_tup is None:
                raise ValueError('Ошибка при получении даты `TaskParse`')

            for item in pars_tup:
                if isinstance(item[1], datetime):
                    string_parse_date, parse_date, _ = item
                    break
            else:
                raise ValueError('Дата не найдена в сообщении, блок `TaskParse`')

            if self.only_datetime_and_message:
                await self.set_user_server_date(parse_date)
                await self.set_only_message(string_parse_date)
                return None

            await self.replace_date_in_message(string_parse_date, parse_date)

            reminder_gpt = ReminderGPT(self.transform_message, self.user, self.chat_id)

            transform_task = asyncio.create_task(reminder_gpt.transform())
            set_date_task = asyncio.create_task(self.set_user_server_date(parse_date))
            transform_message_from_ai, _ = await asyncio.gather(transform_task, set_date_task)

            if not transform_message_from_ai:
                raise ValueError('Ошибка при преобразовании текста в `ReminderGPT`:')

            await self.set_params(transform_message_from_ai)

        except ValueError as error:
            raise ValueError(f'Не распарсил в `TaskParse`:\n{self.inbox_message}.\n{error}') from error
        except Exception as err:
            _, type_err = await handle_exceptions(err)
            if hasattr(err, 'log_traceback') and err.log_traceback:
                err.log_traceback = False
            else:
                traceback_str = traceback.format_exc()
                add_err_trace = f'\n\nТрассировка:\n{traceback_str[-1024:]}'
            raise type_err(f'Ошибка в процессе `TaskParse`:\n{err}{add_err_trace}') from err

    async def replace_date_in_message(self, string_date: str, parse_date: datetime):
        """
        Заменяет дату в тексте сообщения на цифровой формат.

        ### Args:
        - string_date (`str`): Строка с датой для замены.
        - parse_date (`datetime`): Дата для замены.

        """
        self.transform_message = self.inbox_message.replace(string_date, parse_date.strftime('%d.%m.%Y %H:%M')).strip()

    async def set_only_message(self, string_date: str):
        """
        Назначает datetime user_date относительно его ТЗ и datetime server_date по UTC.

        ### Args:
        - parse_date (`datetime`): Дата для преобразования.

        """
        self.only_message = self.inbox_message.replace(string_date, '').strip()

    async def set_user_server_date(self, parse_date: datetime):
        """Назначает datetime user_date относительно его ТЗ и datetime server_date по UTC."""
        user_tz = pytz.timezone(self.time_zone)
        self.user_datetime = user_tz.localize(parse_date)
        self.server_datetime = self.user_datetime.astimezone(self.utc)

    async def set_params(self, transform_message_from_ai: str) -> None:
        """
        Разделяет строку на сообщение и параметры и назначает соответствующие атрибуты.

        ### Args:
        - transform_message_from_ai (`str`): Преобразованное сообщение.

        """
        _, *params = transform_message_from_ai.split('|')
        for param in params:
            if param in self.PERIOD_DIC:
                self.period_repeat = param.strip()
            elif param.isdigit():
                self.delta_time_min = int(param)
            else:
                self.only_message = param.strip()
