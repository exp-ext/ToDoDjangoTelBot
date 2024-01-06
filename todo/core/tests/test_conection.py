from unittest import skip

import redis
from django.conf import settings
from django.test import TestCase
from kombu import Connection, Consumer, Exchange, Queue
from kombu.exceptions import OperationalError


class RedisConnectionTest(TestCase):

    def test_redis_connection(self):
        try:
            connection = settings.REDIS_CLIENT
            connection.ping()
        except redis.ConnectionError as e:
            self.fail(f'Не удалось подключиться к Redis: {e}')

    @skip('Тест не работает')
    def test_celery_connection(self):
        try:
            with Connection(settings.REDIS_URL):
                exchange = Exchange('test_exchange', type='direct')
                queue = Queue('test_queue', exchange, routing_key='test_key')
                consumer = Consumer(Connection(), queue, callbacks=[lambda body, message: None])
                consumer.consume()
        except OperationalError as e:
            self.fail(f"Не удалось подключиться к Celery: {e}")
