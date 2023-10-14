import random
import string

import pytz
from core.models import Create
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from pytils.translit import slugify
from sorl.thumbnail import ImageField


class Group(models.Model):
    chat_id = models.CharField(_('ID группы'), max_length=50, unique=True)
    title = models.CharField(_('Название группы'), max_length=150)
    slug = models.SlugField(unique=True, db_index=True)
    image = ImageField(_('Логотип_группы'), upload_to='group', blank=True)
    description = models.TextField(_('Описание группы'), blank=True, null=True)
    link = models.CharField(_('Пригласительная ссылка для публичных групп'), max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = _('Группа')
        verbose_name_plural = _('Группы')

    def __str__(self):
        return f'~ {self.title}'

    def save(self, *args, **kwargs):
        slug = slugify(self.title)[:30]
        if not slug or Group.objects.filter(Q(slug=slug), ~Q(chat_id=self.chat_id)).exists():
            self.slug = ''.join(random.choices(string.ascii_lowercase, k=15))
        else:
            self.slug = slug
        super().save(*args, **kwargs)


class GroupMailing(models.Model):
    class GroupMailingTypes(models.TextChoices):
        FORISMATIC_QUOTES = 'forismatic_quotes', _('Цитаты')

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_mailing')
    mailing_type = models.CharField(choices=GroupMailingTypes.choices, max_length=100)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор')
        USER = 'user', _('Пользователь')

    tg_id = models.IntegerField(_('id в Телеграмм'), null=True, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('Имя пользователя'),
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
    phone_number = PhoneNumberField(_('номер телефона'), unique=True, null=True, blank=True)
    email = models.EmailField(_('email'), null=True, blank=True)

    birthday = models.DateField(_('Дата рождения'), blank=True, null=True)
    image = ImageField(_('Аватар'), upload_to='users', blank=True)
    favorite_group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name='users')

    role = models.CharField(_('Пользовательская роль'), max_length=10, choices=Role.choices, default=Role.USER)

    validation_key = models.CharField(max_length=28, null=True, blank=True)
    validation_key_time = models.DateTimeField(null=True, blank=True)
    validation_message_id = models.IntegerField(null=True, blank=True)

    is_blocked_bot = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return (
            self.Role == 'admin'
            or self.is_superuser
            or self.is_staff
        )

    def get_full_name(self):
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'.strip()
        return self.username


class Location(Create):
    TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_connections')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='groups_connections')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'group'),
                name='unique_group'
            ),
        )

    def __str__(self):
        return self.group.title
