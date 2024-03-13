import time
from datetime import date as dt
from datetime import datetime, timedelta
from typing import Dict, Iterable, Mapping

import requests
from telegram import Update
from telegram.ext import CallbackContext
from users.views import get_coordinates

from ..cleaner import remove_keyboard
from ..geoservis.support import get_distance


def find_closest_lat_lon(data: Iterable[Mapping[str, float]], v: Mapping[str, float]) -> Dict[str, float]:
    """
    Перебирает координаты в data сравнивая их с v в функции get_distance и возвращает те,
    что имеют минимальное расстояние между собой.
    """
    try:
        return min(
            data,
            key=lambda p: get_distance(p['lat'], p['lon'], v['lat'], v['lon'])
        )
    except Exception as error:
        raise KeyError(error)


def where_to_go(update: Update, context: CallbackContext):
    """Отправляет в чат список событий полученный с api kudago.com."""
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    date_today_int = dt.today()
    date_today = datetime.strftime(date_today_int, '%Y-%m-%d')

    date_yesterday = date_today_int - timedelta(days=1)
    date_yesterday = time.mktime(date_yesterday.timetuple())

    date_tomorrow = date_today_int + timedelta(days=1)
    date_tomorrow = time.mktime(date_tomorrow.timetuple())

    try:
        params = {
            'lang': 'ru',
            'fields': 'slug,name,coords',
        }
        response = requests.get(
            'https://kudago.com/public-api/v1.2/locations/?',
            params=params
        )  # TODO переделать на HTTPX для сокращения библиотек
        city_list = response.json()
    except Exception as error:
        raise KeyError(error)

    city_geo_list = []

    for city in city_list:
        if city['coords']['lat']:
            city_geo_list.append(city['coords'])

    user_id = chat.id
    coordinates = get_coordinates(user_id)

    current_geo = {
        'lat': coordinates.latitude,
        'lon': coordinates.longitude
    }
    nearest_city_geo = find_closest_lat_lon(city_geo_list, current_geo)

    for city in city_list:
        if city['coords'] == nearest_city_geo:
            nearest_city = city['slug']
            city_name = city['name']

    categories = (
        'yarmarki-razvlecheniya-yarmarki,festival,'
        'entertainment,exhibition,holiday,kids'
    )

    try:
        params = {
            'actual_since': date_yesterday,
            'actual_until': date_tomorrow,
            'location': nearest_city,
            'is_free': True,
            'categories': categories,
        }

        response = requests.get(
            'https://kudago.com/public-api/v1.4/events/',
            params=params
        )  # TODO переделать на HTTPX для сокращения библиотек
        next_data = response.json()

        text = (
            '[BCЕ МЕРОПРИЯТИЯ НА СЕГОДНЯ \n'
            f'в ближайшем от Вас городе {city_name}](https://kudago.com/spb/festival/'
            f'?date={date_today}&hide_online=y&only_free=y)\n\n'
        )
        for item in next_data['results']:
            text += (
                f"- {item['title'].capitalize()} [>>>]"
                f"(https://kudago.com/spb/event/{item['slug']}/)\n"
            )
            text += '-------------\n'

        context.bot.send_message(
            chat.id,
            text,
            parse_mode='Markdown',
            message_thread_id=message_thread_id
        )
        remove_keyboard(update, context)

    except Exception as error:
        raise KeyError(error)
