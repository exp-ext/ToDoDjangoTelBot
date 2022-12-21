from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from telegram import Update
from telegram.ext import CallbackContext
from users.views import get_coordinates

from ..cleaner import remove_keyboard
from .support import get_address_from_coords

User = get_user_model()


def my_current_geoposition(update: Update, context: CallbackContext):
    """Отправляет в группу <фаворит> адрес местонахождения."""
    chat = update.effective_chat
    user_id = chat.id
    coordinates = get_coordinates(user_id)

    geo = f"{coordinates.longitude},{coordinates.latitude}"

    user = get_object_or_404(User, username=user_id)

    if user.favorite_group:
        user_id = user.favorite_group.chat_id

    send_text = (
        'Согласно полученных геокоординат, '
        f"{update.effective_chat.full_name} находится:\n"
        f"[{get_address_from_coords(geo)}]"
        "(https://yandex.ru/maps/?whatshere[point]="
        f"{geo}&whatshere[zoom]=17&z=17)\n"
    )
    context.bot.send_message(user_id, send_text, parse_mode='Markdown')
    remove_keyboard(update, context)
