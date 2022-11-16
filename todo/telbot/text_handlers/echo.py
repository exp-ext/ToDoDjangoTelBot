from django.contrib.auth import get_user_model
from telegram import Update
from telegram.ext import CallbackContext

User = get_user_model()


def do_echo(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user_id = update.message.from_user.id
    text = update.message.text

    if User.objects.filter(username=user_id).exists():
        reply_text = 'Ваш ID = {}\n\n{}'.format(chat.id, text)
    else:
        reply_text = (
            'Вы не зарегистрированы! '
            'Введите команду /start чтоб получить пароль к личному кабинету.'
        )
    context.bot.send_message(
        chat.id,
        reply_text
    )
