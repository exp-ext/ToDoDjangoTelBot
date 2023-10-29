import json

from celery import Celery
from django.conf import settings
from stats.models import PostsCounter

redis_client = settings.REDIS_CLIENT
app = Celery()


@app.task
def load_to_database():
    """Считывание данных из redis и загрузка в postgres."""
    byte_agent_posts = redis_client.lrange('list_agent_posts', 0, -1)
    redis_client.delete('list_agent_posts')

    if not byte_agent_posts:
        return 'There are no new statistics to process.'

    decoded_agent_posts = [json.loads(json.loads(byte_str.decode('utf-8'))) for byte_str in byte_agent_posts]
    objs = [PostsCounter(**data) for data in decoded_agent_posts]
    PostsCounter.objects.bulk_create(objs)

    return f'The {len(objs)} post counter data has been loaded into the database'
