import hashlib
import hmac

from django.conf import settings


class HashCheck:
    def __init__(self, data):
        self.hash = data['hash']
        self.secret_key = hashlib.sha256(
            settings.TELEGRAM_TOKEN.encode('utf-8')
        ).digest()
        self.data = {}
        for k, v in data.items():
            if k != 'hash':
                self.data[k] = v

    def data_check_string(self):
        a = sorted(self.data.items())
        res = '\n'.join(map(lambda x: '='.join(x), a))
        return res

    def calc_hash(self):
        msg = bytearray(self.data_check_string(), 'utf-8')
        res = hmac.new(
            self.secret_key, msg=msg, digestmod=hashlib.sha256
        ).hexdigest()
        return res

    def check_hash(self):
        return self.calc_hash() == self.hash
