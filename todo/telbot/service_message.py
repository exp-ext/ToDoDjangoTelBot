from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from .cleaner import process_to_delete_message
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
    sec_before_del = 20
    *params, = chat_id, message_id, sec_before_del
    process_to_delete_message(params)


def cancel(update: Update, _: CallbackContext):
    """Ответ в случае ввода некорректных данных."""
    chat = update.effective_chat
    reply_text = 'Мое дело предложить - Ваше отказаться.'
    send_service_message(chat.id, reply_text, 20)
    return ConversationHandler.END
