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

    ip = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    ref_url = models.CharField(_('реферальная url'), max_length=200, null=True, blank=True)
    block_list = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('статистика по посту')
        verbose_name_plural = _('статистика по постам')

    def __str__(self) -> str:
        return f'{self.post} -> {self.browser}'


class BlockListIP(Create):
    """Модель для хранения IP-адресов в блок-листе.

    ### Attributes:
    - ip (GenericIPAddressField): IP-адрес, который может быть как IPv4, так и IPv6.
    - block_list (BooleanField): Флаг, указывающий на наличие IP-адреса в блок-листе.

    ### Meta:
    - ordering (tuple): Порядок сортировки записей по умолчанию.

    ### Example:
        Использование модели BlockListIP:

        ```python
        # Создание записи в блок-листе для IP-адреса '192.168.1.1'
        ip_entry = BlockListIP(ip='192.168.1.1', block_list=True)
        ip_entry.save()
        ```
    """
    ip = models.GenericIPAddressField(protocol='both', null=True, blank=True)
    block_list = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('IP в блок листе')
        verbose_name_plural = _('IP в блок листах')

    def __str__(self) -> str:
        return f'{self.ip} -> {self.block_list}'
