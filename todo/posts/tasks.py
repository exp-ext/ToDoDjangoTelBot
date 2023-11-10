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
    contents = []

    base_node_db = PostContents.objects.create(post=instance, anchor=instance.title, is_root=True)

    for tag in soup.find_all(['h2', 'h4']):
        if tag.name == 'h2':
            text = text.replace(str(tag), f'<section id="{tag.text}">{str(tag)}</section>')
            current_node_db = PostContents.objects.create(post=instance, anchor=tag.text, parent=base_node_db)
        elif tag.name == 'h4':
            text = text.replace(str(tag), f'<section id="{tag.text}">{str(tag)}</section>')
            contents.append(
                PostContents(
                    post=instance,
                    anchor=tag.text,
                    parent=current_node_db,
                )
            )

    if contents:
        PostContents.objects.bulk_create(contents)
    instance.text = text
    instance.save()
    return 'Создано оглавление для поста '
