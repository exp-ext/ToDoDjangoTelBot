from multiprocessing import Process
from typing import Any, Iterable

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)
from telegram.ext import CallbackContext
from users.models import Group, GroupConnections
from users.views import Signup, set_coordinates

from .cleaner import delete_messages_by_time
from .service_message import send_service_message

User = get_user_model()


def assign_group(update: Update):
    """Присваивание группы юзеру."""
    chat = update.effective_chat
    user_id = update.message.from_user.id

    if chat.type != 'private':
        user = get_object_or_404(
            User.objects.select_related('favorite_group'),
            username=user_id
        )
        group = Group.objects.get_or_create(
            chat_id=chat.id,
            title=chat.title
        )[0]

        if not user.favorite_group:
            user.favorite_group = group
            user.save()

        GroupConnections.objects.get_or_create(
            user=user,
            group=group
        )


def build_menu(buttons: Iterable[Any], n_cols: int,
               header_buttons=None,
               footer_buttons=None) -> list[Any]:
    """Функция шаблон для построения кнопок"""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append[(footer_buttons)]
    return menu


def main_menu(update: Update, context: CallbackContext) -> None:
    """Кнопки основного меню на экран."""
    chat = update.effective_chat
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if User.objects.filter(username=user_id).exists():
        button_list = [
            InlineKeyboardButton('💬 добавить запись',
                                 callback_data='add_first_step'),
            InlineKeyboardButton('❌ удалить запись',
                                 callback_data='del_first_step'),
            InlineKeyboardButton('🚼 календарь рождений',
                                 callback_data='show_birthday'),
            InlineKeyboardButton('📅 планы на дату',
                                 callback_data='show_first_step'),
            InlineKeyboardButton('📝 все планы',
                                 callback_data='show_all_notes'),
            InlineKeyboardButton('🎭 анекдот',
                                 callback_data='show_joke'),
            InlineKeyboardButton('😼 картинки с котиками',
                                 callback_data='get_cat_image'),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

        menu_text = (
            "* 💡  ГЛАВНОЕ МЕНЮ  💡 *".center(25, " ")
            + "\n"
            + f"для пользователя {user_name}".center(25, " ")
        )
        context.bot.send_message(
            chat.id,
            menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        assign_group(update)
    else:
        reply_text = (
            f'{update.effective_user.first_name}, пожалуйста пройдите '
            f'[процедуру регистрации]({context.bot.link}) 🔆'
        )
        send_service_message(chat.id, reply_text)


def private_menu(update: Update, context: CallbackContext) -> None:
    """Кнопки меню погоды только в личном чате с ботом"""
    chat = update.effective_chat
    user_id = update.message.from_user.id

    if (User.objects.filter(username=user_id).exists()
            and chat.type == 'private'):
        button_list = [
            InlineKeyboardButton('🌈 погода сейчас',
                                 callback_data='weather_per_day'),
            InlineKeyboardButton('☔️ прогноз погоды на 4 дня',
                                 callback_data='weather'),
            InlineKeyboardButton('🛰 моя позиция для группы',
                                 callback_data='my_position'),
            InlineKeyboardButton('🏄 список мероприятий поблизости',
                                 callback_data='show_festivals'),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

        menu_text = ('* 💡  МЕНЮ  💡 *'.center(28, '~'))
        context.bot.send_message(
            chat.id,
            menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        set_coordinates(update, context)
    else:
        raise_text = (
            f'{update.message.from_user.first_name}, функции геолокации '
            f'работают только в [private chat]({context.bot.link}) с ботом.'
        )
        message_id = context.bot.send_message(chat.id, raise_text).message_id
        *params, = user_id, message_id, 20
        p1 = Process(target=delete_messages_by_time, args=(params,))
        p1.start()
        assign_group(update)


def ask_registration(update: Update, context: CallbackContext) -> None:
    """Создаём кнопку для получения координат в его личном чате."""
    chat = update.effective_chat
    first_name = update.message.from_user.first_name
    if chat.type == 'private':
        button_list = [
            KeyboardButton('Показать меню 📋', request_location=True),
        ]
        reply_markup = ReplyKeyboardMarkup(
            build_menu(button_list, n_cols=1),
            resize_keyboard=True
        )
        menu_text = (
            f'Приветствую Вас, {first_name}!\n'
            'Внизу появилась кнопка с новыми функциями.\n'
            'Первым делом нажмите на неё и получите погоду '
            'в Вашем местонахождении для настройки часового пояса.'
        )
        context.bot.send_message(
            chat.id,
            menu_text,
            reply_markup=reply_markup
        )
        Signup().register(update, context)
