from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Dispatcher, Filters,
                          MessageHandler)

from .gpt.chat_distributor import (get_answer_chat_gpt_person,
                                            get_answer_chat_gpt_public)
from .gpt.image_gen import first_step_get_image, get_image_dall_e
from .parse.kudago import where_to_go
from .geoservis.positions import my_current_geoposition
from .geoservis.weather import current_weather, weather_forecast
from .loader import bot
from .menus import (ask_auth, ask_registration, main_menu, private_menu,
                    reset_bot_history, show_my_links)
from .notes.add_notes import add_notes, first_step_add
from .notes.del_notes import del_notes, first_step_dell
from .notes.show_notes import (first_step_show, show_all_notes, show_at_date,
                               show_birthday)
from .notes.stereography import send_audio_transcription
from .parse.jokes import show_joke
from .service_message import cancel


def setup_dispatcher(dp: Dispatcher):
    """
    Добавление обработчиков событий из Telegram
    """
    # основное меню и его Handler's
    dp.add_handler(
        CommandHandler('main_menu', main_menu)
    )
    dp.add_handler(
        CommandHandler('reset_bot_history', reset_bot_history)
    )
    dp.add_handler(
        CommandHandler('start', ask_registration)
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_add, pattern='^add_first_step$')],
            states={'add_note': [MessageHandler(Filters.text, add_notes)]},
            fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)]
        )
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_show, pattern='^show_first_step$')],
            states={'show_note': [MessageHandler(Filters.text, show_at_date)]},
            fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)]
        )
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_dell, pattern='^del_first_step$')],
            states={'del_note': [MessageHandler(Filters.text, del_notes)]},
            fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)]
        )
    )
    dp.add_handler(
        CallbackQueryHandler(show_all_notes, pattern='^show_all_notes$')
    )
    dp.add_handler(
        CallbackQueryHandler(show_birthday, pattern='^show_birthday$')
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(first_step_get_image, pattern='^gen_image_first$')],
            states={'image_gen': [MessageHandler(Filters.text, get_image_dall_e)]},
            fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)]
        )
    )
    dp.add_handler(
        CallbackQueryHandler(show_joke, pattern='^show_joke$')
    )
    dp.add_handler(
        MessageHandler(Filters.location, private_menu)
    )
    dp.add_handler(
        MessageHandler(Filters.contact, ask_auth)
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
    dp.add_handler(
        MessageHandler(Filters.regex(r'Ева|Eva'), get_answer_chat_gpt_public)
    )
    dp.add_handler(
        CommandHandler('show_my_links', show_my_links)
    )
    dp.add_handler(
        MessageHandler(Filters.voice, send_audio_transcription)
    )
    dp.add_handler(
        MessageHandler(Filters.text, get_answer_chat_gpt_person)
    )
    return dp


dispatcher = setup_dispatcher(
    Dispatcher(bot, update_queue=None, workers=4, use_context=True)
)
