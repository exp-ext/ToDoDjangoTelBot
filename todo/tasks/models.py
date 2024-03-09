import os
import uuid
from datetime import timedelta

from core.models import Create
from core.tasks import delete_image_in_bucket, delete_image_in_local
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from sorl.thumbnail import ImageField
from users.models import Group

User = get_user_model()
USE_S3 = settings.USE_S3


def custom_uuid_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('tasks/', filename)


class Task(Create):
    """
    Модель для хранения задач и напоминаний.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с задачей.
    - group (`ForeignKey`, optional): Группа, связанная с задачей.
    - server_datetime (`DateTimeField`): Дата и время задачи на сервере.
    - picture_link (`CharField`, optional): Ссылка на картинку.
    - image (`ImageField`, optional): Картинка для напоминания.
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
        verbose_name=_('группа'),
        help_text=_('если выбрать группу, то оповещение будет в ней')
    )
    server_datetime = models.DateTimeField(_('Дата и время для хранения на сервере'))
    picture_link = models.CharField(
        _('ссылка на картинку'),
        help_text=_('ссылка в формате https://domen.ru/fantasy.jpg'),
        max_length=200,
        blank=True
    )
    image = ImageField(_('ваша картинка'), upload_to=custom_uuid_filename, blank=True, help_text=_('приоритетной для напоминания считается именно эта картинка'))
    text = CKEditor5Field(_('текст напоминания'), blank=True, config_name='tasks', help_text=_('введите текст напоминания'))
    remind_min = models.IntegerField(
        _('оповестить за ... минут'),
        default=120,
        help_text=_('оповестить за ... минут до наступления события')
    )
    remind_at = models.DateTimeField(_('время срабатывания оповещения'))
    reminder_period = models.CharField(
        _('периодичность напоминания'),
        max_length=1,
        choices=Repeat.choices,
        default=Repeat.NEVER,
        help_text=_('выберите период повторения напоминания')
    )
    it_birthday = models.BooleanField(_('день рождения'))

    class Meta:
        verbose_name = _('напоминание')
        verbose_name_plural = _('напоминания')
        ordering = ('server_datetime',)

    def __str__(self):
        return f'#{self.user} - напоминание на {self.remind_at}'

    def save(self, *args, **kwargs):
        self.remind_at = self.server_datetime - timedelta(minutes=self.remind_min)
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=Task)
def delete_task_image(sender, instance, **kwargs):
    """
    Удаление связанной картинки перед удалением экземпляра Task.
    В случае использования S3 создается задача для удаления с бакета.
    """
    if instance.image:
        if USE_S3:
            if hasattr(instance.image, 'url'):
                delete_image_in_bucket.apply_async(args=(instance.image.url,), countdown=120)
        else:
            delete_image_in_local.delay(instance.image.path)


@receiver(pre_save, sender=Task)
def delete_old_task_image(sender, instance, **kwargs):
    """
    Удаление связанной картинки при изменении экземпляра Task.
    В случае использования S3 создается задача для удаления с бакета.
    """
    if instance.pk:
        old_instance = Task.objects.filter(pk=instance.pk).first()
        if old_instance.image and old_instance.image != instance.image:
            if USE_S3:
                if hasattr(old_instance.image, 'url'):
                    delete_image_in_bucket.delay(old_instance.image.url)
            else:
                delete_image_in_local.delay(old_instance.image.path)
