from typing import Mapping

from telegram import BotCommand

from .loader import bot

COMMANDS: Mapping[str, Mapping[str, str]] = {
    'en': {
        'main_menu': '📲 Main bot menu',
        'reset_bot_history': '✂️ Reset request history',
        'show_my_links': '📥 Show my links'
    },
    'ru': {
        'main_menu': '📲 Общее меню бота',
        'reset_bot_history': '✂️ Сбросить историю запросов',
        'show_my_links': '📥 Показать основные ссылки'
    }
}


def set_up_commands() -> None:
    """Переназначение команд бота."""

    for lc in COMMANDS:
        bot.set_my_commands(
            language_code=lc,
            commands=[
                BotCommand(key, item) for key, item in COMMANDS[lc].items()
            ]
        )
    return True


# set_up_commands()
