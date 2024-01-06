import telegram
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


@app.task(ignore_result=True)
def send_message_to_chat(tg_id: int, message: str, reply_to_message_id: int = None, parse_mode_markdown: bool = False) -> None:
    """Отправляет сообщение через Telegram бота.

    Эта функция отправляет сообщение пользователю или группе в Telegram. В случае, если отправка
    сообщения вызывает исключение telegram.error.BadRequest, функция пытается отправить сообщение
    без форматирования Markdown. Любые другие исключения перенаправляются на указанный ADMIN_ID.

    ### Args:
    - tg_id (`int`): Telegram ID пользователя или группы для отправки сообщения.
    - message (`str`): Текст сообщения для отправки.
    - reply_to_message_id (`int`, optional): ID сообщения, на которое должен быть дан ответ. По умолчанию None.
    - parse_mode_markdown (`bool`, optional): Указывает, использовать ли Markdown форматирование. По умолчанию False.

    ### Returns:
    - None: Функция не возвращает значение.
    """
    parse_mode = ParseMode.MARKDOWN if parse_mode_markdown else None
    try:
        bot.send_message(
            chat_id=tg_id,
            text=message,
            parse_mode=parse_mode,
            reply_to_message_id=reply_to_message_id,
        )
    except telegram.error.BadRequest:
        bot.send_message(
            chat_id=tg_id,
            text=message,
            reply_to_message_id=reply_to_message_id,
        )
    except Exception as err:
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f'Ошибка TGB при отправке ответа: {str(err)[:1024]}',
        )
