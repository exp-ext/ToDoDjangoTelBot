from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from sorl.thumbnail import ImageField
from users.models import Group

User = get_user_model()


class Post(Create):
    title = models.CharField(
        verbose_name='Заголовок поста',
        max_length=100,
        blank=False,
        null=False,
    )
    text = models.TextField(
        verbose_name='Текст поста',
        blank=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа, к которой будет относиться пост'
    )
    image = ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return self.title[:20]


class Comment(Create):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарии',
        help_text='Комментарии поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=('author', 'user'),
            name='unique_follower'),
        )

    def __str__(self):
        return f'{self.user} follows {self.author}'
