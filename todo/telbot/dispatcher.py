from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Dispatcher, Filters,
                          MessageHandler)

from todo.settings import DEBUG

from .external_api.kudago import where_to_go
from .external_api.pastime import get_new_image
from .geoservis.positions import my_current_geoposition
from .geoservis.weather import current_weather, weather_forecast
from .loader import bot
from .menus import ask_registration, main_menu, private_menu
from .message.add_notes import add_notes, first_step_add
from .message.del_notes import del_notes, first_step_dell
from .message.show_notes import (first_step_show, show_all_notes, show_at_date,
                                 show_birthday)
from .parse.jokes import show_joke
from .service_message import cancel
from .text_handlers.echo import do_echo


def setup_dispatcher(dp: Dispatcher):
    """
    Добавление обработчиков событий из Telegram
    """
    # команды
    dp.add_handler(
        CommandHandler('ask_registration', ask_registration)
    )

    # основное меню и его Handler's
    dp.add_handler(
        CommandHandler('main_menu', main_menu)
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_add,
                                               pattern='^first_step_add$')],
            states={
                'user_note': [MessageHandler(Filters.text, add_notes)]
            },
            fallbacks=[MessageHandler(
                Filters.regex('^(end)$'),
                cancel
            )]
        )
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_show,
                                               pattern='^first_step_show$')],
            states={
                'show_note': [MessageHandler(Filters.text, show_at_date)]
            },
            fallbacks=[MessageHandler(
                Filters.regex('^(end)$'),
                cancel
            )]
        )
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_dell,
                                               pattern='^first_step_del$')],
            states={
                'user_del_note': [MessageHandler(Filters.text, del_notes)]
            },
            fallbacks=[MessageHandler(
                Filters.regex('^(end)$'),
                cancel
            )]
        )
    )
    dp.add_handler(
        CallbackQueryHandler(show_all_notes, pattern='^show_all_notes$')
    )
    dp.add_handler(
        CallbackQueryHandler(show_birthday, pattern='^show_birthday$')
    )
    dp.add_handler(
        CallbackQueryHandler(get_new_image, pattern='^get_cat_image$')
    )
    dp.add_handler(
        CallbackQueryHandler(show_joke, pattern='^show_joke$')
    )
    # меню только для private и его Handler's
    dp.add_handler(
        MessageHandler(Filters.location, private_menu)
    )
    dp.add_handler(
        CallbackQueryHandler(current_weather, pattern='^weather_per_day$')
    )
    dp.add_handler(
        CallbackQueryHandler(weather_forecast, pattern='^weather$')
    )
    dp.add_handler(
        CallbackQueryHandler(my_current_geoposition, pattern='^my_position$')
    )
    dp.add_handler(
        CallbackQueryHandler(where_to_go, pattern='^show_festivals$')
    )

    # эхо
    dp.add_handler(
        MessageHandler(Filters.text, do_echo)
    )

    return dp


n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(
    Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True)
)
