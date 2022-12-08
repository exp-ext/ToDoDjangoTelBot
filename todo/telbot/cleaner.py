import re
import threading
import time
from typing import Sequence

from telegram import Update
from telegram.ext import CallbackContext

from .commands import COMMANDS
from .loader import bot


def clear_commands(update: Update) -> None:
    """Удаление команд бота из чата."""
    try:
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        text = ''

        if update.message.location:
            text = 'delete'
        else:
            if update.message.text:
                text = update.message.text.replace('/', '')
                command = re.findall(r'(.*?)(?=\@)', text)
                if command:
                    text = command[0]

        if text in COMMANDS['en'] or text == 'delete':
            bot.delete_message(chat_id, message_id)

    except Exception as error:
        print(f'!!! Ошибка в модуле clear_commands: {error}')
        # raise KeyError(error)


def remove_keyboard(update: Update, context: CallbackContext) -> None:
    """
    Удаление клавиатуры после нажатия.
        Принимает:
    - update (:obj:`Update`)
    - context (:obj:`CallbackContext`)
    """
    chat = update.effective_chat
    del_menu_id = update.effective_message.message_id
    context.bot.delete_message(chat.id, del_menu_id)


def delete_messages_by_time(params: Sequence[int]) -> None:
    """
    Удаление сообщения по таймеру.
    Параметры:
    - chat id (:obj:`int` | :obj:`str`)
    - message id (:obj:`int` | :obj:`str`)
    - seconds before deletion (:obj:`int`)
    """
    chat_id: int
    message_id: int
    seconds: int
    chat_id, message_id, seconds = params
    time.sleep(seconds)
    bot.delete_message(chat_id, message_id)


def process_to_delete_message(params):
    """
    Запускает дополнительный процесс для функции
    :obj:`delete_messages_by_time`.
    """
    thread = threading.Thread(target=delete_messages_by_time, args=(params,))
    thread.start()
