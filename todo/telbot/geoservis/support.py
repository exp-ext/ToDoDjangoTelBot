from math import asin, cos, radians, sin, sqrt

import requests

from todo.settings import YANDEX_GEO_API_TOKEN


def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
        Вычисляет расстояние в километрах между двумя точками,
        учитывая окружность Земли.
        https://en.wikipedia.org/wiki/Haversine_formula
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6367 * c


def get_address_from_coords(coords: str) -> str:
    """
    Возвращает адрес местонахождения, полученный через api geocode-maps.yandex.
    """
    params = {
        "apikey": YANDEX_GEO_API_TOKEN,
        "format": "json",
        "lang": "ru_RU",
        "kind": "house",
        "geocode": coords,
    }
    try:
        r = requests.get(
            url="https://geocode-maps.yandex.ru/1.x/",
            params=params
        )  # TODO переделать на HTTPX для сокращения библиотек
        json_data = r.json()

        return (
            json_data["response"]["GeoObjectCollection"]["featureMember"]
            [0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]
            ["AddressDetails"]["Country"]["AddressLine"]
        )

    except Exception as error:
        raise KeyError(error)


def status_weather(description_weather: str) -> str:
    """Добавление картинки в описание погоды."""
    try:
        dict_weather = {
            'ясно': ' ☀️ ясно',
            'переменная облачность': ' 🌤 переменная облачность',
            'небольшая облачность': ' 🌤 переменная облачность',
            'облачно с прояснениями': ' ⛅️ облачно с прояснениями',
            'пасмурно': ' ☁️ пасмурно',
            'небольшой дождь': ' 🌦 небольшой дождь',
            'сильный дождь': ' ⛈ сильный дождь',
            'дождь': ' 🌧 дождь',
        }
        return dict_weather[description_weather]

    except Exception:
        return description_weather
