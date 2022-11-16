import pytz
from core.models import Create
from django.contrib.auth.models import AbstractUser
from django.db import models
from pytils.translit import slugify


class Group(models.Model):
    chat_id = models.CharField(
        verbose_name='ID группы',
        max_length=50,
        unique=True
    )
    title = models.TextField(
        verbose_name='Название группы',
        max_length=150,
    )
    slug = models.SlugField(
        unique=True,
        db_index=True
    )
    image = models.ImageField(
        verbose_name='Логотип_группы',
        upload_to='group/',
        blank=True
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return f'#{self.title}: {self.chat_id}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)


class User(AbstractUser):
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=256,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=256,
        null=True,
        blank=True
    )
    birthday = models.DateField(
        verbose_name='Дата рождения',
        null=True
    )
    image = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/',
        blank=True
    )
    favorite_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users'
    )

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'@{self.username}'


class Location(Create):
    TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()

    timezone = models.CharField(
        max_length=32,
        choices=TIMEZONES,
        default='Europe/Moscow'
    )

    def __str__(self):
        return (f"user: {self.user}, updated at "
                f"{self.created_at.strftime('(%H:%M, %d %B %Y)')}")


class GroupConnections(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='groups_connections'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='users_connections'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=('user', 'group'),
            name='unique_group'),
        )

    def __str__(self):
        return f'{self.user} состоит в группе {self.group}'
