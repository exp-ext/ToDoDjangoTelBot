import re

from telegram import Update
from telegram.ext import CallbackContext

from todo.celery import app

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

    except Exception:
        text = (
            'Для корректной работы, я должен быть администратором группы! '
            'Иначе я не смогу удалять подобные технические сообщения.'
        )
        bot.send_message(chat_id, text)


def remove_keyboard(update: Update, context: CallbackContext) -> None:
    """
    Удаление клавиатуры после нажатия.
    ### Args:
    - update (:obj:`Update`)
    - context (:obj:`CallbackContext`)
    """
    chat = update.effective_chat
    del_menu_id = update.effective_message.message_id
    try:
        context.bot.delete_message(chat.id, del_menu_id)
    except Exception as error:
        raise KeyError(error)


@app.task(ignore_result=True)
def delete_messages_by_time(chat_id: int, message_id: int) -> None:
    """
    Удаление сообщения.
    ### Args:
    - chat_id (:obj:`int` | :obj:`str`)
    - message_id (:obj:`int` | :obj:`str`)
    """
    try:
        # bot.delete_message(chat_id, message_id)
        pass
    except Exception as error:
        raise KeyError(error)
