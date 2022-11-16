from typing import Mapping

from telegram import Bot, BotCommand

from .start import bot

COMMANDS: Mapping[str, Mapping[str, str]] = {
    'en': {
        'main_menu': '📲 Main menu of bot',
        'ask_registration': '📍Register',
    },
    'ru': {
        'main_menu': '📲 Основное меню бота',
        'ask_registration': '📍Пройти регистрацию',
    }
}


def set_up_commands(bot_instance: Bot) -> None:
    bot_instance.delete_my_commands()
    for lang_code in COMMANDS:
        bot_instance.set_my_commands(
            language_code=lang_code,
            commands=[
                BotCommand(c, d) for c, d in COMMANDS[lang_code].items()
            ]
        )


set_up_commands(bot)
