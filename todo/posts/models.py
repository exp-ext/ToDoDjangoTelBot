from bs4 import BeautifulSoup
from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from pytils.translit import slugify
from sorl.thumbnail import ImageField
from treebeard.al_tree import AL_Node
from users.models import Group

User = get_user_model()


class PostTags(models.Model):
    """Модель для хранения тегов постов.

    ### Attributes:
    - title (str): Название тега поста (максимум 50 символов).
    - description (str, optional): Краткое описание тега поста.
    - slug (str): Уникальный идентификатор тега, используемый в URL.

    """
    title = models.CharField(_('тэг поста'), max_length=50, unique=True)
    description = models.TextField(_('краткое описание'), blank=True, null=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)

    class Meta:
        verbose_name = _('тэг')
        verbose_name_plural = _('тэги')

    def __str__(self):
        return self.title[50]


@receiver(pre_save, sender=PostTags)
def pre_save_group(sender, instance, *args, **kwargs):
    """Генерируем уникальный slug на основе title, если не задан."""
    if not instance.slug:
        instance.slug = slugify(instance.title)


class Post(Create):
    """Модель для хранения постов.

    ### Class:
    - Moderation (`TextChoices`): Вложенный класс, представляющий статусы модерации.

    ### Attributes:
    - title (`CharField`): Заголовок поста.
    - text (`CKEditor5Field`): Текст поста.
    - author (`ForeignKey`): Автор поста.
    - group (`ForeignKey`, optional): Группа, к которой будет относиться пост.
    - image (`ImageField`): Картинка, прикрепленная к посту.

    """
    class Moderation(models.TextChoices):
        WAITING = 'WT', _('ОЖИДАЕТ ПОДТВЕРЖДЕНИЯ')
        PASSED = 'PS', _('МОДЕРАЦИЯ ПРОЙДЕНА')
        UNMODERATED = 'NM', _('МОДЕРАЦИЯ НЕ ПРОЙДЕНА')

    title = models.CharField(_('заголовок поста'), max_length=80)
    text = CKEditor5Field(_('текст поста'), blank=True, config_name='extends')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name=_('автор'))
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name=_('группа, к которой будет относиться пост')
    )
    image = ImageField(_('картинка'), upload_to='posts/', blank=True)
    tags = models.ManyToManyField(to=PostTags, related_name='posts')
    moderation = models.CharField(_('модерация заметки'), max_length=2, choices=Moderation.choices, default=Moderation.WAITING)

    class Meta:
        verbose_name = _('пост')
        verbose_name_plural = _('посты')
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return self.title[:20]


@receiver(pre_save, sender=Post)
def pre_save_group(sender, instance, *args, **kwargs):
    """Пре-обработка текста поста перед сохранением.

    ### Args:
    - sender: Класс модели, отправляющий сигнал (Post).
    - instance: Экземпляр модели поста.
    - *args: Дополнительные аргументы.
    - **kwargs: Дополнительные именованные аргументы.
    """
    text = instance.text
    soup = BeautifulSoup(text, features="html.parser")

    for tag in soup.find_all(['h2', 'h4']):
        tag_text = tag.text.strip()
        search_tag = str(tag).replace('\xa0', '&nbsp;')
        text = text.replace(search_tag, f'<section id="{tag_text}">{str(tag)}</section>')

    instance.text = text


@receiver(post_save, sender=Post)
def after_product_creation(sender, instance, created, **kwargs):
    """Обработка после сохранения поста.

    ### Args:
    - sender: Класс модели, отправляющий сигнал (Post).
    - instance: Экземпляр модели поста.
    - created (bool): Флаг, указывающий, был ли объект создан.
    - **kwargs: Дополнительные именованные аргументы.
    """
    text = instance.text
    soup = BeautifulSoup(text, features="html.parser")
    current_node_db = None
    instance.contents.all().delete()
    base_node_db = PostContents.objects.create(post=instance, anchor=instance.title, is_root=True)

    for tag in soup.find_all(['h2', 'h4']):
        tag_text = tag.text.strip()

        if tag.name == 'h2':
            current_node_db = PostContents.objects.create(post=instance, anchor=tag_text, parent=base_node_db)
        elif tag.name == 'h4':
            PostContents.objects.create(post=instance, anchor=tag_text, parent=current_node_db if current_node_db else base_node_db)


class PostContents(AL_Node):
    """Модель для хранения оглавления комментариев к посту.

    ### Attributes:
    - post (Post): Связь с постом, к которому относится оглавление.
    - title (str): Заголовок оглавления (максимум 250 символов).
    - anchor (str): Якорь оглавления (максимум 250 символов).
    - parent (PostContents, optional): Связь с родительским оглавлением (если есть).
    - desc (str): Описание оглавления (максимум 255 символов).
    - is_root (bool): Флаг, указывающий, является ли оглавление корневым.
    - node_order_by (list): Порядок сортировки узлов.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='contents', verbose_name=_('пост'))
    anchor = models.CharField(_('заголовок/глава/раздел'), max_length=80)

    parent = models.ForeignKey('self', related_name='children_set', null=True, db_index=True, on_delete=models.CASCADE)
    is_root = models.BooleanField(default=False)
    node_order_by = ['id',]

    class Meta:
        verbose_name = _('оглавление')
        verbose_name_plural = _('оглавления')

    def __str__(self):
        return f'{self.post.id} - {self.anchor}'


class Comment(Create):
    """Модель для хранения комментариев к постам.

    ### Attributes:
    - post (`ForeignKey`): Пост, к которому относится комментарий.
    - author (`ForeignKey`): Автор комментария.
    - text (`TextField`): Текст комментария.

    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('комментарии'),
        help_text=_('комментарии поста')
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name=_('Автор'))
    text = models.TextField(_('текст комментария'), help_text=_('введите текст комментария'))

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    """Модель для отслеживания подписок пользователей на других пользователей.

    ### Attributes:
    - user (`ForeignKey`): Пользователь, который подписывается.
    - author (`ForeignKey`): Пользователь, на которого подписываются.

    ### Constraints:
    - unique_follower: Уникальное сочетание (author, user).

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'user'),
                name='unique_follower'
            ),
        )

    def __str__(self):
        return f'{self.user} follows {self.author}'
