from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from sorl.thumbnail import ImageField
from users.models import Group

User = get_user_model()


class Post(Create):
    """
    Модель для хранения постов.

    ### Fields:
    - title (`CharField`): Заголовок поста.
    - text (`CKEditor5Field`): Текст поста.
    - author (`ForeignKey`): Автор поста.
    - group (`ForeignKey`, optional): Группа, к которой будет относиться пост.
    - image (`ImageField`): Картинка, прикрепленная к посту.

    """
    title = models.CharField(_('заголовок поста'), max_length=100)
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

    class Meta:
        verbose_name = _('пост')
        verbose_name_plural = _('посты')
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return self.title[:20]


class Comment(Create):
    """
    Модель для хранения комментариев к постам.

    ### Fields:
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
    """
    Модель для отслеживания подписок пользователей на других пользователей.

    ### Fields:
    - user (`ForeignKey`): Пользователь, который подписывается.
    - author (`ForeignKey`): Пользователь, на которого подписываются.

    ### Constraints:
    - unique_follower: Уникальное сочетание (author, user).

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=('author', 'user'),
            name='unique_follower'),
        )

    def __str__(self):
        return f'{self.user} follows {self.author}'
