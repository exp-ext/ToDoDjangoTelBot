from datetime import timedelta

from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Group

User = get_user_model()


class Task(Create):
    """
    Модель для хранения задач и напоминаний.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с задачей.
    - group (`ForeignKey`, optional): Группа, связанная с задачей.
    - server_datetime (`DateTimeField`): Дата и время задачи на сервере.
    - picture_link (`CharField`, optional): Ссылка на картинку.
    - text (`TextField`): Текст напоминания.
    - remind_min (`IntegerField`): Оповестить за ... минут.
    - remind_at (`DateTimeField`): Время срабатывания оповещения.
    - reminder_period (`CharField`): Периодичность напоминания.
    - it_birthday (`BooleanField`): День рождения.

    """
    class Repeat(models.TextChoices):
        NEVER = 'N', _('Никогда')
        EVERY_DAY = 'D', _('Каждый день')
        EVERY_WEEK = 'W', _('Каждую неделю')
        EVERY_MONTH = 'M', _('Каждый месяц')
        EVERY_YEAR = 'Y', _('Каждый год')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True,
        verbose_name=_('Группа'),
        help_text=_('Если выбрать группу, то оповещение будет в ней.')
    )
    server_datetime = models.DateTimeField(_('Дата и время для хранения на сервере'))
    picture_link = models.CharField(
        _('Ссылка на картинку'),
        help_text=_('Ссылка в формате https://domen.ru/fantasy.jpg'),
        max_length=200,
        blank=True
    )
    text = models.TextField(_('Текст напоминания'), help_text=_('Введите текст напоминания.'))
    remind_min = models.IntegerField(
        _('Оповестить за ... минут'),
        default=120,
        help_text=_('Оповестить за ... минут до наступления события.')
    )
    remind_at = models.DateTimeField(_('Время срабатывания оповещения'))
    reminder_period = models.CharField(
        _('Периодичность напоминания'),
        max_length=1,
        choices=Repeat.choices,
        default=Repeat.NEVER,
        help_text=_('Выберите период повторения напоминания.')
    )
    it_birthday = models.BooleanField(_('День рождения'))

    class Meta:
        verbose_name = _('Напоминание')
        verbose_name_plural = _('Напоминания')
        ordering = ('server_datetime',)

    def __str__(self):
        return f'#{self.user} - напоминание на {self.remind_at}'

    def save(self, *args, **kwargs):
        self.remind_at = self.server_datetime - timedelta(minutes=self.remind_min)
        super().save(*args, **kwargs)
