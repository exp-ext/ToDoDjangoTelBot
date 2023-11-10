from typing import Any, Dict

from bs4 import BeautifulSoup
from core.serializers import ModelDataSerializer
from posts.models import PostContents

from todo.celery import app


@app.task
def create_contents(post_model: Dict[str, Any]) -> str:
    instance = ModelDataSerializer.deserialize(post_model)
    text = instance.text
    soup = BeautifulSoup(text, features="html.parser")
    current_node_db = None
    instance.contents.all().delete()

    base_node_db = PostContents.objects.create(post=instance, anchor=instance.title, is_root=True)

    for tag in soup.find_all(['h2', 'h4']):
        tag_text = tag.text.strip()
        search_tag = str(tag).replace('\xa0', '&nbsp;')
        text = text.replace(search_tag, f'<section id="{tag_text}">{str(tag)}</section>')

        if tag.name == 'h2':
            current_node_db = PostContents.objects.create(post=instance, anchor=tag_text, parent=base_node_db)
        elif tag.name == 'h4':
            PostContents.objects.create(
                post=instance,
                anchor=tag_text,
                parent=current_node_db if current_node_db else base_node_db,
            )

    instance.text = text
    instance.save()
    return 'Создано оглавление для поста '
