import base64
import os
import pickle
import urllib.request

import requests
from celery import Celery
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

app = Celery()

LOGIN_DNS_API = os.getenv('LOGIN_DNS_API')
PASSWORD_DNS_API = os.getenv('PASSWORD_DNS_API')
HOST_FOR_DNS = os.getenv('HOST_FOR_DNS')
FILE_WITH_IP_DIR = settings.BASE_DIR


def read_file() -> str:
    """Считываем из файла для проверки."""
    try:
        with open(f'{FILE_WITH_IP_DIR}/file_with_ip.pickle', 'rb') as fb:
            return pickle.load(fb)
    except OSError:
        raise OSError


def write_file(file_with_ip: str) -> None:
    """Записываем в файл для проверки на следующем цикле."""
    with open(f'{FILE_WITH_IP_DIR}/file_with_ip.pickle', 'wb') as fb:
        pickle.dump(file_with_ip, fb)


def get_current_ip() -> str:
    """Возвращает IP адрес соединения."""
    try:
        ip = requests.get('https://api.ipify.org').content.decode('utf8')
    except Exception:
        ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    return ip


def check_tokens():
    """Возвращает результат проверки констант для API в окружении."""
    return all((LOGIN_DNS_API, PASSWORD_DNS_API, HOST_FOR_DNS))


@app.task
def set_ip_to_dns() -> str:
    """
    Назначение IP адреса для домена через API.
    https://www.nic.ru/help/dinamicheskij-dns-dlya-razrabotchikov_4391.html
    """

    if check_tokens() is False:
        return 'No API-DNS connection variables'

    current_ip = get_current_ip()
    last_ip = read_file()

    if current_ip == last_ip:
        return 'No change'

    write_file(current_ip)
    api_url = 'https://api.nic.ru/dyndns/update'
    params = {
        'hostname': HOST_FOR_DNS,
        'myip': current_ip
    }
    user_pass = LOGIN_DNS_API + ':' + PASSWORD_DNS_API
    b64val = base64.b64encode(user_pass.encode()).decode()
    headers = {
        'Authorization': 'Basic %s' % b64val
    }
    set_ip = requests.get(api_url, headers=headers, params=params)
    return f'Результат запроса на назначение IP для host: {set_ip}'
