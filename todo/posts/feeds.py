from django.db.models import Q
from yaturbo.toolbox import YandexTurboFeed

from .models import Post


class TurboFeed(YandexTurboFeed):

    title = 'YourToDo - практическое программирование'
    link = 'http://www.yourtodo.ru/'
    description = 'Исследуйте разнообразие тем и статей по программированию, включая Python, Django, Data Science и многое другое на YourToDo.ru!'

    turbo_sanitize = False

    def items(self):
        return (
            Post.objects
            .select_related('author', 'group')
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS')[:1]
        )

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return item.author.get_full_name()

    def item_author_email(self, item):
        return item.author.email

    def item_description(self, item):
        return item.short_description

    def item_pubdate(self, item):
        return item.created_at

    def item_turbo(self, item):
        return item.html_turbo()

    def item_extended_html(self, item):
        return 'true'
