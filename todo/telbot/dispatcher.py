from telegram.ext import (CallbackQueryHandler, CommandHandler, Dispatcher,
                          Filters, MessageHandler)

from todo.settings import DEBUG

from .external_api.kudago import where_to_go
from .external_api.pastime import get_new_image
from .geoservis.positions import my_current_geoposition
from .geoservis.weather import current_weather, weather_forecast
from .menus import ask_registration, main_menu, private_menu
# from .text_handlers.echo import do_echo
from .message.handling import add_notes
from .parse.jokes import show_joke
from .start import bot


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
        MessageHandler(Filters.text, add_notes)
    )

    # # admin commands
    # dp.add_handler(CommandHandler("admin", admin_handlers.admin))
    # dp.add_handler(
    #   CommandHandler("stats", admin_handlers.stats)
    # )
    # dp.add_handler(
    #   CommandHandler('export_users', admin_handlers.export_users)
    # )

    # # location
    # dp.add_handler(
    #   CommandHandler("ask_location", location_handlers.ask_for_location)
    # )
    # dp.add_handler(
    #   MessageHandler(Filters.location, location_handlers.location_handler)
    # )

    # # files
    # dp.add_handler(MessageHandler(
    #     Filters.animation, files.show_file_id,
    # ))

    # # handling errors
    # dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    # EXAMPLES FOR HANDLERS

    # dp.add_handler(
    #    MessageHandler(Filters.text, <function_handler>)
    # )

    # dp.add_handler(
    #    MessageHandler(Filters.document, <function_handler>)
    # )

    # dp.add_handler(
    #    CallbackQueryHandler(<function_handler>, pattern="^r\d+_\d+")
    # )

    # dp.add_handler(MessageHandler(
    #     Filters.chat(chat_id=int(TELEGRAM_FILESTORAGE_ID)),
    #       & Filters.forwarded
    #       & (Filters.photo | Filters.video | Filters.animation),
    #     <function_handler>,
    # ))

    return dp


n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(
    Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True)
)
