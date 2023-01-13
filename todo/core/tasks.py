import base64
import os
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
        raise Exception('No API-DNS connection variables')

    get_api_url = 'https://api.nic.ru/dyndns/checkip'
    current_dns_ip = requests.get(get_api_url)

    current_local_ip = get_current_ip()

    if current_local_ip in current_dns_ip.text:
        return 'IP у DNS провайдера соответствует текущему.'

    set_api_url = 'https://api.nic.ru/dyndns/update'
    params = {
        'hostname': HOST_FOR_DNS,
        'myip': current_local_ip
    }
    user_pass = LOGIN_DNS_API + ':' + PASSWORD_DNS_API
    b64val = base64.b64encode(user_pass.encode()).decode()
    headers = {
        'Authorization': 'Basic %s' % b64val
    }
    set_ip = requests.get(set_api_url, headers=headers, params=params)
    return (
        f'На хост у DNS провайдера назначен новый IP: {current_local_ip}. '
        f'Ответ сервера DNS: {set_ip.text}'
    )
