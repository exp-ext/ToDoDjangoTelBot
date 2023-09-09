from typing import Mapping

from telegram import Bot, BotCommand

# from .loader import bot

COMMANDS: Mapping[str, Mapping[str, str]] = {
    'en': {
        'main_menu': '📲 Main menu of bot',
        'ask_registration': '📍 Register',
        'show_my_links': '📥 Show my links'
    },
    'ru': {
        'main_menu': '📲 Основное меню бота',
        'ask_registration': '📍Пройти регистрацию',
        'show_my_links': '📥 Показать основные ссылки'
    }
}


def set_up_commands(bot_instance: Bot) -> None:
    """Переназначение команд бота."""

    # bot_instance.delete_my_commands()
    for lc in COMMANDS:
        bot_instance.set_my_commands(
            language_code=lc,
            commands=[
                BotCommand(key, item) for key, item in COMMANDS[lc].items()
            ]
        )


# set_up_commands(bot)
