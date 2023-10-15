from typing import Any, Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)
from telegram.ext import CallbackContext
from users.views import Authentication, set_coordinates

from .checking import check_registration
from .cleaner import delete_messages_by_time

User = get_user_model()


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
    user_name = update.effective_user.first_name

    answers = {
        '': (f'{update.effective_user.first_name}, пожалуйста пройдите по '
             f'ссылке [для прохождения процедуры регистрации]'
             f'({context.bot.link}) 🔆')
    }

    if check_registration(update, context, answers):
        button_list = [
            InlineKeyboardButton('💬 добавить запись', callback_data='add_first_step'),
            InlineKeyboardButton('❌ удалить запись', callback_data='del_first_step'),
            InlineKeyboardButton('🚼 календарь рождений', callback_data='show_birthday'),
            InlineKeyboardButton('📅 планы на дату', callback_data='show_first_step'),
            InlineKeyboardButton('📝 все планы', callback_data='show_all_notes'),
            InlineKeyboardButton('🎭 анекдот', callback_data='show_joke'),
            InlineKeyboardButton('🌁 генерировать картинку по описанию', callback_data='gen_image_first'),
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


def private_menu(update: Update, context: CallbackContext) -> None:
    """Кнопки меню погоды только в личном чате с ботом"""
    chat = update.effective_chat

    answers = {
        '': (f'{update.message.from_user.first_name}, функции геолокации '
             f'работают только в [private chat]({context.bot.link}) с ботом.')
    }

    if check_registration(update, context, answers):
        button_list = [
            InlineKeyboardButton('🌈 погода сейчас', callback_data='weather_per_day'),
            InlineKeyboardButton('☔️ прогноз погоды на 4 дня', callback_data='weather'),
            InlineKeyboardButton('🛰 моя позиция для группы', callback_data='my_position'),
            InlineKeyboardButton('🏄 список мероприятий поблизости', callback_data='show_festivals'),
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


def ask_registration(update: Update, context: CallbackContext) -> None:
    """Регистрация пользователя."""
    chat = update.effective_chat
    first_name = update.message.from_user.first_name
    if chat.type == 'private':
        button_list = [
            KeyboardButton('меню геофункций 📡', request_location=True),
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
        Authentication(update, context).register()


def show_my_links(update: Update, context: CallbackContext):
    """Выводит ссылки на бота и на основной сайт."""
    chat = update.effective_chat
    button_list = [
        InlineKeyboardButton(text='Телеграмм',
                             url=context.bot.link),
        InlineKeyboardButton(text='Вебсайт',
                             url=f'https://www.{settings.DOMAIN}/')
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    menu_text = 'личный кабинет системы -->'
    message_id = context.bot.send_message(
        chat.id,
        menu_text,
        reply_markup=reply_markup
    ).message_id
    delete_messages_by_time.apply_async(
        args=[chat.id, message_id],
        countdown=40
    )


def ask_auth(update: Update, context: CallbackContext) -> None:
    """Получаем ссылку для авторизации на сайте."""
    chat = update.effective_chat

    answers = {
        '': ('Для начала необходимо пройти регистрацию.')
    }

    if check_registration(update, context, answers) and chat.type == 'private':
        Authentication(update, context).authorization()
