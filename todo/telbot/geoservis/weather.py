from datetime import datetime

import requests
from telegram import Update
from telegram.ext import CallbackContext
from users.views import get_coordinates

from todo.settings import OW_API_TOKEN

from ..cleaner import remove_keyboard
from .support import status_weather


def current_weather(update: Update, context: CallbackContext):
    """Выводит в чат текущую погоду по координатам."""
    chat = update.effective_chat
    user_id = chat.id
    coordinates = get_coordinates(user_id)
    try:
        res = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                'lat': coordinates.latitude,
                'lon': coordinates.longitude,
                'units': 'metric',
                'lang': 'ru',
                'APPID': OW_API_TOKEN
            }
        )
        data = res.json()

        wind_directions = (
            "Сев",
            "Сев-Вост",
            "Вост",
            "Юго-Вост",
            "Южный",
            "Юго-Зап",
            "Зап",
            "Сев-Зап"
        )
        wind_speed = int(data['wind']['speed'])
        direction = int((wind_speed + 22.5) // 45 % 8)
        pressure = round(int(data['main']['pressure'] * 0.750063755419211))

        weather = [
            f" *{status_weather(data['weather'][0]['description'])}*",
            f" 💧 влажность: *{data['main']['humidity']}*%",
            f" 🌀 давление:   *{pressure}*мм рт.ст",
            f" 💨 ветер: *{wind_speed}м/сек ⤗ {wind_directions[direction]}*",
            f" 🌡 текущая: *{'{0:+3.0f}'.format(data['main']['temp'])}*°C",
            f" 🥶 мин:  *{'{0:+3.0f}'.format(data['main']['temp_min'])}*°C",
            f" 🥵 макс: *{'{0:+3.0f}'.format(data['main']['temp_max'])}*°C"
        ]

        st = "По данным ближайшего метеоцентра сейчас на улице:\n"
        max_len = max(len(x) for x in weather)
        for item in weather:
            st += f'{item.rjust(max_len, "~")}\n'

        context.bot.send_message(chat.id, st, parse_mode='Markdown')
        remove_keyboard(update, context)

    except Exception as error:
        raise KeyError(error)


def weather_forecast(update: Update, context: CallbackContext):
    """Выводит прогноз погоды на 4 дня по последним User координатам."""
    chat = update.effective_chat
    user_id = chat.id
    coordinates = get_coordinates(user_id)

    try:
        res = requests.get(
            "http://api.openweathermap.org/data/2.5/forecast?",
            params={
                'lat': coordinates.latitude,
                'lon': coordinates.longitude,
                'units': 'metric',
                'lang': 'ru',
                'APPID': OW_API_TOKEN
            }
        )
        data = res.json()

        time_zone = int(data['city']['timezone'])

        sunrise_time = datetime.utcfromtimestamp(
            int(data['city']['sunrise']) + time_zone
        )
        sunset_time = datetime.utcfromtimestamp(
            int(data['city']['sunset']) + time_zone
        )
        city = data['city']['name']
        text_weather = f"Прогноз в месте с названием\n*{city}*:\n"

        for record in range(0, 40, 8):
            temp_max_min_day = []
            temp_max_min_night = []

            date_j = data['list'][record]['dt_txt'][:10]
            text_weather += f"*{date_j}*\n".rjust(25, '~')

            description = status_weather(
                data['list'][record]['weather'][0]['description']
            )
            text_weather += f"*{description}*\n"

            for i in range(40):
                if (data['list'][i]['dt_txt'][:10]
                        == data['list'][record]['dt_txt'][:10]):

                    if (sunset_time.hour
                            > int(data['list'][i]['dt_txt'][11:13])
                            > sunrise_time.hour):

                        temp_max_min_day.append(
                            data['list'][i]['main']['temp_min']
                        )
                        temp_max_min_day.append(
                            data['list'][i]['main']['temp_max']
                        )
                    else:
                        temp_max_min_night.append(
                            data['list'][i]['main']['temp_min']
                        )
                        temp_max_min_night.append(
                            data['list'][i]['main']['temp_max']
                        )

            if len(temp_max_min_day) > 0:
                text_weather += (
                    f"🌡🌞 *{'{0:+3.0f}'.format(max(temp_max_min_day))}* "
                    f"... *{'{0:+3.0f}'.format(min(temp_max_min_day))}*°C\n"
                )

            if len(temp_max_min_night) > 0:
                text_weather += (
                    f"      🌙 *{'{0:+3.0f}'.format(max(temp_max_min_night))}* "
                    f"... *{'{0:+3.0f}'.format(min(temp_max_min_night))}*°C\n"
                )
            coeff_celsia = 0.750063755419211
            pressure_c = int(
                data['list'][record]['main']['pressure'] * coeff_celsia
            )
            text_weather += f"давление *{pressure_c}*мм рт.ст\n"

        text_weather += "-\n".rjust(30, '-')
        text_weather += f"      ВОСХОД в *{sunrise_time.strftime('%H:%M')}*\n"
        text_weather += f"      ЗАКАТ     в *{sunset_time.strftime('%H:%M')}*"

        context.bot.send_message(chat.id, text_weather, parse_mode='Markdown')
        remove_keyboard(update, context)

    except Exception as error:
        raise KeyError(error)
