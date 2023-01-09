import base64

import requests
from core.tasks import (HOST_FOR_DNS, LOGIN_DNS_API, PASSWORD_DNS_API,
                        check_tokens, get_current_ip)


def set_ip_to_dns() -> str:
    """
    Назначение IP адреса для домена через API.
    https://www.nic.ru/help/dinamicheskij-dns-dlya-razrabotchikov_4391.html
    """
    if check_tokens() is False:
        raise Exception('No API-DNS connection variables')

    current_ip = get_current_ip()

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
