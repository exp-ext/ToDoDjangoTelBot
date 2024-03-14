from bs4 import BeautifulSoup
from core.models import Create, CreateUpdater
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from pytils.translit import slugify
from sorl.thumbnail import ImageField
from treebeard.mp_tree import MP_Node
from users.models import Group

from .tasks import delete_image_in_bucket, delete_image_in_local

User = get_user_model()
USE_S3 = settings.USE_S3


class PostTags(models.Model):
    """Модель для хранения тегов постов.

    ### Attributes:
    - title (str): Название тега поста (максимум 80 символов).
    - description (str, optional): Краткое описание тега поста.
    - slug (str): Уникальный идентификатор тега, используемый в URL.

    """
    title = models.CharField(_('тэг поста'), max_length=80, unique=True)
    description = models.TextField(_('краткое описание'), blank=True, null=True)
    slug = models.SlugField(max_length=80, unique=True, db_index=True)
    image = ImageField(_('картинка'), upload_to='tags/', blank=True)

    class Meta:
        verbose_name = _('тэг')
        verbose_name_plural = _('тэги')

    def __str__(self):
        return self.title


@receiver(pre_save, sender=PostTags)
def pre_save_post_tags(sender, instance, *args, **kwargs):
    """Генерируем уникальный slug на основе title, если не задан."""
    if not instance.slug:
        instance.slug = slugify(instance.title)


class Post(CreateUpdater):
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

    slug = models.SlugField(_('slug поста'), max_length=80, unique=True)
    title = models.CharField(_('заголовок поста'), max_length=80, unique=True)
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
    short_description = models.CharField(_('короткое описание поста'), max_length=160, null=True, blank=True)

    class Meta:
        verbose_name = _('пост')
        verbose_name_plural = _('посты')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['author_id']),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'post_identifier_slug': self.slug})

    def html_turbo(self):
        root_contents = self.contents.filter(depth=1).first()
        contents = PostContents.dump_bulk(root_contents) if root_contents else None
        context = {
            'post': self,
            'contents': contents[0].get('children', None) if contents else None,
        }
        html_content = render_to_string('turbo/post_detail.html', context)
        return html_content


@receiver(pre_save, sender=Post)
def pre_save_post(sender, instance, *args, **kwargs):
    """Пре-обработка текста поста перед сохранением.

    ### Args:
    - sender: Класс модели, отправляющий сигнал (Post).
    - instance: Экземпляр модели поста.
    - *args: Дополнительные аргументы.
    - **kwargs: Дополнительные именованные аргументы.
    """
    if instance.pk:
        old_instance = Post.objects.only('image').filter(pk=instance.pk).first()
        if getattr(old_instance, 'image', None) and getattr(instance, 'image', None) and old_instance.image.name.split('/')[-1] != instance.image.name.split('/')[-1]:
            if USE_S3:
                if hasattr(old_instance.image, 'url'):
                    delete_image_in_bucket.delay(old_instance.image.url)
            else:
                delete_image_in_local.delay(old_instance.image.path)

    text = instance.text
    soup = BeautifulSoup(text, features="html.parser")

    for tag in soup.find_all(['h2', 'h4']):
        tag_text = tag.text.strip()
        search_tag = str(tag).replace('\xa0', '&nbsp;')
        text = text.replace(search_tag, f'<section id="{tag_text}">{str(tag)}</section>')

    instance.text = text
    instance.slug = slugify(instance.title)


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
    instance.contents.all().delete()
    base_node = PostContents.add_root(post=instance, anchor=instance.title)

    current_node = None
    for tag in soup.find_all(['h2', 'h4']):
        anchor = tag.text.strip()

        if tag.name == 'h2':
            current_node = base_node.add_child(post=instance, anchor=anchor)
        elif tag.name == 'h4' and current_node:
            current_node.add_child(post=instance, anchor=anchor)
        else:
            base_node.add_child(post=instance, anchor=anchor)


@receiver(pre_delete, sender=Post)
def delete_post_image(sender, instance, **kwargs):
    """
    Удаление связанной картинки перед удалением экземпляра Post.
    В случае использования S3 создается задача для удаления с бакета.
    """
    if instance.image:
        if USE_S3:
            delete_image_in_bucket.delay(instance.image.url)
        else:
            delete_image_in_local.delay(instance.image.path)


class PostContents(MP_Node):
    """Модель для хранения оглавления комментариев к посту.

    ### Attributes:
    - post (Post): Связь с постом, к которому относится оглавление.
    - anchor (str): Якорь оглавления (максимум 250 символов).
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='contents', verbose_name=_('пост'))
    anchor = models.CharField(_('заголовок/глава/раздел'), max_length=250)

    class Meta:
        verbose_name = _('оглавление')
        verbose_name_plural = _('оглавления')
        ordering = ('id',)

    def __str__(self):
        return f'{self.post} - {self.anchor}'


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
