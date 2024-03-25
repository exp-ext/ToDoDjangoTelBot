import json

from celery import Celery
from django.conf import settings
from django.db import transaction
from stats.models import PostsCounter

redis_client = settings.REDIS_CLIENT
app = Celery()


@app.task
def load_to_database():
    """Считывание данных из redis и загрузка в postgres."""
    pipeline = redis_client.pipeline()
    pipeline.lrange('list_agent_posts', 0, -1)
    pipeline.delete('list_agent_posts')
    byte_agent_posts, _ = pipeline.execute()

    if not byte_agent_posts:
        return 'There are no new statistics to process.'

    decoded_agent_posts = (json.loads(byte_str.decode('utf-8')) for byte_str in byte_agent_posts)

    with transaction.atomic():
        objs = [PostsCounter(**data) for data in decoded_agent_posts]
        PostsCounter.objects.bulk_create(objs, batch_size=1000)

    return f'The {len(objs)} post counter data has been loaded into the database.'
