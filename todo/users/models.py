import random
import string

import pytz
from core.models import Create
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from pytils.translit import slugify
from sorl.thumbnail import ImageField


class Group(models.Model):
    """
    Модель для описания группы.

    ### Fields:
    - chat_id (`CharField`): ID группы (уникальное значение).
    - title (`CharField`): Название группы.
    - slug (`SlugField`): Уникальный идентификатор группы.
    - image (`ImageField`): Логотип группы.
    - description (`TextField`): Описание группы.
    - link (`CharField`): Пригласительная ссылка для публичных групп.

    """
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


@receiver(pre_save, sender=Group)
def pre_save_group(sender, instance, *args, **kwargs):
    """Генерируем уникальный slug на основе title, если не задан."""
    if not instance.slug:
        slug = slugify(instance.title)[:30]
        if not slug or Group.objects.filter(Q(slug=slug), ~Q(chat_id=instance.chat_id)).exists():
            instance.slug = ''.join(random.choices(string.ascii_lowercase, k=15))


class GroupMailing(models.Model):
    """
    Модель для связи групп и типов рассылок.

    ### Fields:
    - group (`ForeignKey`): Ссылка на группу.
    - mailing_type (`CharField`): Тип рассылки (FORISMATIC_QUOTES и др.).

    """
    class GroupMailingTypes(models.TextChoices):
        FORISMATIC_QUOTES = 'forismatic_quotes', _('Цитаты')

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_mailing')
    mailing_type = models.CharField(choices=GroupMailingTypes.choices, max_length=100)


class User(AbstractUser):
    """
    Модель пользователя с расширенными полями.

    ### Fields:
    - tg_id (`IntegerField`): ID в Телеграмм.
    - username (`CharField`): Имя пользователя.
    - phone_number (`PhoneNumberField`): Номер телефона.
    - email (`EmailField`): Email адрес.
    - birthday (`DateField`): Дата рождения.
    - image (`ImageField`): Аватар пользователя.
    - favorite_group (`ForeignKey`): Любимая группа пользователя.
    - role (`CharField`): Пользовательская роль (ADMIN или USER).
    - validation_key (`CharField`): Ключ для валидации.
    - validation_key_time (`DateTimeField`): Время валидации ключа.
    - validation_message_id (`IntegerField`): ID валидационного сообщения.
    - is_blocked_bot (`BooleanField`): Флаг заблокированного бота.
    - created_at (`DateTimeField`): Дата создания.

    ### Relationships:
    - favorite_group (`Group`): Любимая группа пользователя.

    ### Methods:
    - is_admin: Проверяет, является ли пользователь администратором.
    - get_full_name: Возвращает полное имя пользователя.

    """
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
    """
    Модель для хранения информации о местоположении пользователя.

    ### Fields:
    - user (`ForeignKey`): Ссылка на пользователя, к которому привязано местоположение.
    - latitude (`FloatField`): Широта местоположения.
    - longitude (`FloatField`): Долгота местоположения.
    - timezone (`CharField`): Временная зона для местоположения.

    ### Timezones:
    - Временные зоны, доступные для выбора, включая все зоны, предоставленные библиотекой pytz.

    ### Attributes:
    - TIMEZONES (`tuple`): Кортеж с доступными временными зонами.

    ### Default Timezone:
    - По умолчанию, устанавливается временная зона 'Europe/Moscow'.
    """
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
    """
    Модель для хранения связей между пользователями и группами.

    ### Fields:
    - user (`ForeignKey`): Ссылка на пользователя, принадлежащего группе.
    - group (`ForeignKey`): Ссылка на группу, к которой привязан пользователь.

    ### Relationships:
    - user (`User`): Связанный пользователь.
    - group (`Group`): Связанная группа.

    """
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
