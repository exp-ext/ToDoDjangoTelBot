from django.contrib.auth import get_user_model
from telegram import Update
from telegram.ext import CallbackContext

User = get_user_model()


def do_echo(update: Update, context: CallbackContext):
    chat = update.effective_chat
    tg_user = update.message.from_user
    text = update.message.text

    if User.objects.filter(username=tg_user.username).exists():
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
