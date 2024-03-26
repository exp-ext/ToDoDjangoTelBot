import traceback

import telegram
from core.re_compile import NUMBER_BYTE_OFFSET
from django.conf import settings
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from todo.celery import app

from .cleaner import delete_messages_by_time
from .loader import bot

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


def send_service_message(chat_id: int, reply_text: str, parse_mode: str = None, message_thread_id: int = None) -> None:
    """
    Отправляет сообщение в чат и запускает процесс удаления сообщения
    с отсрочкой в 20 секунд.
    - chat_id (:obj:`int` | :obj:`str`) - ID чата.
    - reply_text (:obj:`str`) - текс сообщения
    - parse_mode (:obj:`str`) - Markdown or HTML.
    - message_thread_id (:obj:`str`) - номер темы для супергрупп
    """
    message_id = bot.send_message(
        chat_id,
        reply_text,
        parse_mode,
        message_thread_id=message_thread_id
    ).message_id
    delete_messages_by_time.apply_async(
        args=[chat_id, message_id],
        countdown=20
    )


def cancel(update: Update, _: CallbackContext):
    """Ответ в случае ввода некорректных данных."""
    chat = update.effective_chat
    reply_text = 'Мое дело предложить - Ваше отказаться.'
    send_service_message(chat.id, reply_text, 20)
    return ConversationHandler.END


def find_byte_offset(message):
    """
    Ищет в сообщении числовое значение после 'byte offset'.
    Возвращает найденное значение как целое число или None, если совпадение не найдено.
    """
    match = NUMBER_BYTE_OFFSET.search(message)
    if match:
        return int(match.group(1))
    return None


def delete_at_byte_offset(text, offset):
    """
    Удаляет текст на позиции `offset`.
    """
    byte_text = text.encode('utf-8')
    modified_byte_text = byte_text[:offset] + byte_text[offset + 1:]
    return modified_byte_text.decode('utf-8')


@app.task(ignore_result=True)
def send_message_to_chat(tg_id: int, message: str, reply_to_message_id: int = None, parse_mode: ParseMode = None, retry_count: int = 3) -> None:
    """
    Отправляет сообщение через Telegram бота с возможностью исправления и повторной отправки при ошибке.

    ### Args:
    - tg_id (`int`): Идентификатор чата в Telegram.
    - message (`str`): Текст сообщения.
    - reply_to_message_id (`int`, optional): Идентификатор сообщения, на которое нужно ответить.
    - parse_mode (`ParseMode`, optional): Режим парсинга сообщения.
    - retry_count (`int`, optional): Количество попыток отправки при ошибке.

    """
    if retry_count < 1:
        bot.send_message(
            chat_id=tg_id,
            text=message,
            reply_to_message_id=reply_to_message_id,
        )
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f'Ошибка в `send_message_to_chat` BadRequest\n\nMessage:\n{message}',
        )
        return

    try:
        bot.send_message(
            chat_id=tg_id,
            text=message,
            parse_mode=parse_mode,
            reply_to_message_id=reply_to_message_id,
        )
    except telegram.error.BadRequest as err:
        error_message = str(err)
        offset = find_byte_offset(error_message)
        if offset is not None:
            message = delete_at_byte_offset(message, offset)
            send_message_to_chat(tg_id, message, reply_to_message_id, parse_mode, retry_count - 1)

    except Exception as err:
        traceback_str = traceback.format_exc()
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f'Необработанная ошибка в `send_message_to_chat`: {str(err)}\n\nТрассировка:\n{traceback_str[-1024:]}'
        )
