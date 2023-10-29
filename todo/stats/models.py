from core.models import Create
from django.db import models
from django.utils.translation import gettext_lazy as _
from posts.models import Post


class PostsCounter(Create):
    """
    Модель для отслеживания просмотров постов.

    ### Attributes:
    - post (Post): Ссылка на пост, для которого отслеживается количество просмотров.
    - browser (str): Название браузера, используемого пользователем.
    - browser_version (str): Версия браузера.
    - os (str): Операционная система пользователя.
    - is_bot (bool): Флаг, указывающий, является ли пользователь ботом.
    - is_mobile (bool): Флаг, указывающий, что пользователь использует мобильное устройство.
    - is_pc (bool): Флаг, указывающий, что пользователь использует ПК.
    - is_tablet (bool): Флаг, указывающий, что пользователь использует планшет.
    - is_touch_capable (bool): Флаг, указывающий, что устройство поддерживает сенсорный ввод.

    ### Meta:
    - ordering: Порядок сортировки объектов по дате создания.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='view_count')
    browser = models.CharField(_('браузер'), max_length=200)
    os = models.CharField(_('операционная система'), max_length=200)
    is_bot = models.BooleanField(default=False)
    is_mobile = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_touch_capable = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('статистика по посту')
        verbose_name_plural = _('статистика по постам')

    def __str__(self) -> str:
        return f'{self.post} -> {self.browser}'
