from django.db.models import Q
from posts.models import Post
from yaturbo.toolbox import YandexTurboFeed


class TurboFeed(YandexTurboFeed):

    title = 'YourToDo - Практическое программирование'
    link = '/'
    description = 'Исследуйте разнообразие тем и статей по программированию, включая Python, Django, Data Science и многое другое на YourToDo!'

    turbo_sanitize = True

    def items(self):
        return (
            Post.objects
            .select_related('author', 'group')
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS')
            .order_by('group')
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.short_description

    def item_link(self, item):
        return item.get_absolute_url()

    def item_turbo(self, item):
        return item.text
