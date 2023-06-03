import random
import string

import pytz
from core.models import Create
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from pytils.translit import slugify
from sorl.thumbnail import ImageField


class Group(models.Model):
    chat_id = models.CharField(
        verbose_name='ID группы',
        max_length=50,
        unique=True
    )
    title = models.CharField(
        verbose_name='Название группы',
        max_length=150,
    )
    slug = models.SlugField(
        unique=True,
        db_index=True
    )
    image = ImageField(
        verbose_name='Логотип_группы',
        upload_to='group',
        blank=True
    )
    description = models.TextField(
        verbose_name='Описание группы',
        blank=True,
        null=True
    )
    link = models.CharField(
        verbose_name='Пригласительная ссылка для публичных групп',
        max_length=150,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return f'~ {self.title}'

    def save(self, *args, **kwargs):
        slug = slugify(self.title)[:30]
        if (not slug
            or Group.objects.filter(
                Q(slug=slug),
                ~Q(chat_id=self.chat_id)).exists()):
            self.slug = ''.join(
                random.choices(string.ascii_lowercase, k=15)
            )
        else:
            self.slug = slug
        super().save(*args, **kwargs)


class GroupMailing(models.Model):
    class GroupMailingTypes(models.TextChoices):
        FORISMATIC_QUOTES = 'forismatic_quotes', _('Цитаты')

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_mailing'
    )
    mailing_type = models.CharField(
        choices=GroupMailingTypes.choices,
        max_length=100
    )


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор')
        USER = 'user', _('Пользователь')

    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('id полученное в Телеграмм'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. '
            'Letters, digits and @/./+/-/_ only.'
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    birthday = models.DateField(
        verbose_name='Дата рождения',
        blank=True,
        null=True
    )
    image = ImageField(
        verbose_name='Аватар',
        upload_to='users',
        blank=True
    )
    favorite_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users'
    )
    role = models.CharField(
        verbose_name='Пользовательская роль',
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )

    is_blocked_bot = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return (
            self.Role == 'admin'
            or self.is_superuser
            or self.is_staff
        )


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
        return (
            f"user: {self.user}, updated at "
            f"{self.created_at.strftime('(%H:%M, %d %B %Y)')}"
        )


class GroupConnections(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='groups_connections'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='groups_connections'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'group'),
                name='unique_group'
            ),
        )

    def __str__(self):
        return f'{self.group}'
