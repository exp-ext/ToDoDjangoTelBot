from datetime import timedelta

from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Group

User = get_user_model()


class WishList(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    wish = models.CharField(
        verbose_name='Желание',
        max_length=256
    )
    donator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='donate_objects',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Желание'
        verbose_name_plural = 'Желания'
        constraints = (models.UniqueConstraint(
            fields=('user', 'wish'),
            name='unique_wish'),
        )

    def __str__(self):
        return f'#{self.user} мечтает о {self.wish}'


class CelebratoryFriend(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    friend = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    gift = models.BooleanField(default=False)
    remind_in = models.IntegerField(
        verbose_name='Оповестить за ... дней',
        help_text='Оповестить за ... дней до наступления события.'
    )

    class Meta:
        verbose_name = 'Подписка на праздники друзей'
        constraints = (models.UniqueConstraint(
            fields=('user', 'friend'),
            name='unique_follower'),
        )

    def __str__(self):
        return f'#{self.user} следит за {self.friend}'


class Task(models.Model):

    class Repeat(models.TextChoices):
        NEVER = 'N', _('Никогда')
        EVERY_DAY = 'D', _('Каждый день')
        EVERY_WEEK = 'W', _('Каждую неделю')
        EVERY_MONTH = 'M', _('Каждый месяц')
        EVERY_YEAR = 'Y', _('Каждый год')

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Если выбрать группу, то оповещение будет в ней.'
    )
    server_datetime = models.DateTimeField(
        verbose_name='Дата и время для хранения на сервере'
    )
    text = models.TextField(
        verbose_name='Текст напоминания',
        help_text='Введите текст напоминания.'
    )
    remind_min = models.IntegerField(
        default=120,
        verbose_name='Оповестить за ... минут',
        help_text='Оповестить за ... минут до наступления события.'
    )
    remind_at = models.DateTimeField(
        verbose_name='Время срабатывания оповещения'
    )
    reminder_period = models.CharField(
        max_length=1,
        choices=Repeat.choices,
        default=Repeat.NEVER,
        verbose_name='Периодичность напоминания',
        help_text='Выберите период повторения напоминания.'
    )
    it_birthday = models.BooleanField(
        verbose_name='День рождения'
    )

    class Meta:
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        ordering = ('server_datetime',)

    def __str__(self):
        return f'#{self.user} - напоминание на {self.remind_at}'

    def save(self, *args, **kwargs):
        self.remind_at = (
            self.server_datetime - timedelta(minutes=self.remind_min)
        )
        super().save(*args, **kwargs)
