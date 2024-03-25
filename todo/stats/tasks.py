import json

from celery import Celery
from django.conf import settings
from django.db import transaction
from posts.models import Post
from stats.models import PostsCounter

redis_client = settings.REDIS_CLIENT
app = Celery()


@app.task
def load_to_database():
    """Считывание данных из Redis и загрузка в PostgreSQL, предварительно проверив существование post_id."""
    pipeline = redis_client.pipeline()
    pipeline.lrange('list_agent_posts', 0, -1)
    pipeline.delete('list_agent_posts')
    byte_agent_posts, _ = pipeline.execute()

    if not byte_agent_posts:
        return 'There are no new statistics to process.'

    decoded_agent_posts = [json.loads(byte_str.decode('utf-8')) for byte_str in byte_agent_posts]
    post_ids = {data['post_id'] for data in decoded_agent_posts}
    existing_post_ids = set(Post.objects.filter(id__in=post_ids).values_list('id', flat=True))

    valid_objs = [PostsCounter(**data) for data in decoded_agent_posts if data['post_id'] in existing_post_ids]

    with transaction.atomic():
        PostsCounter.objects.bulk_create(valid_objs, batch_size=1000)

    return f'The {len(valid_objs)} post counter data has been loaded into the database.'
