from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from .cleaner import delete_messages_by_time
from .loader import bot


def send_service_message(chat_id: int, reply_text: str,
                         parse_mode: str = None) -> None:
    """
    Отправляет сообщение в чат и запускает процесс удаления сообщения
    с отсрочкой в 20 секунд.
    - chat_id (:obj:`int` | :obj:`str`) - ID чата.
    - reply_text (:obj:`str`) - текс сообщения
    - parse_mode (:obj:`str`) - Markdown or HTML.
    """
    message_id = bot.send_message(chat_id, reply_text, parse_mode).message_id
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
