from asgiref.sync import sync_to_async
from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.manager import BaseManager
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AsyncManager(BaseManager.from_queryset(models.QuerySet)):
    """
    Менеджер модели, который добавляет поддержку асинхронных
    операций с базой данных.
    """


class HistoryAI(Create):
    """
    Модель для хранения истории вопросов и ответов AI.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с историей.
    - question (`TextField`): Вопрос, заданный пользователем.
    - question_tokens (`PositiveIntegerField`): Количество токенов в вопросе (может быть null).
    - answer (`TextField`): Ответ, сгенерированный AI.
    - answer_tokens (`PositiveIntegerField`): Количество токенов в ответе (может быть null).

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history_ai', null=True, blank=True)
    room_group_name = models.CharField(_('WEB чат'), max_length=128, null=True, blank=True)
    question = models.TextField(_('Вопрос'))
    question_tokens = models.PositiveIntegerField(null=True)
    answer = models.TextField(_('Ответ'))
    answer_tokens = models.PositiveIntegerField(null=True)

    class Meta:
        verbose_name = _('История запросов к ИИ')
        verbose_name_plural = _('История запросов к ИИ')
        ordering = ('created_at',)

    def __str__(self):
        return f'User: {self.user}, Question: {self.question}'

    @sync_to_async
    def save(self, *args, **kwargs):
        """
        Переопределение метода save() для поддержки асинхронного
        сохранения объекта в базе данных.
        """
        return super().save(*args, **kwargs)


class HistoryDALLE(Create):
    """
    Модель для хранения истории запросов и ответов от DALL·E.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с историей.
    - question (`TextField`): Запрос, заданный пользователем.
    - answer (`JSONField`): Ответ, полученный от DALL·E.

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history_dalle')
    question = models.TextField(_('Запрос'))
    answer = models.JSONField(_('Ответ'))

    class Meta:
        verbose_name = _('История запросов к Dalle')
        verbose_name_plural = _('История запросов к Dalle')
        ordering = ('created_at',)

    def __str__(self):
        return f'User: {self.user}, Question: {self.question}'


class HistoryWhisper(Create):
    """
    Модель для хранения истории аудиотранскрибции.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с историей.
    - file_id (`CharField`): Идентификатор файла.
    - transcription (`TextField`): Текстовая транскрибция аудио.

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history_whisper')
    file_id = models.CharField(_('Id файла'), max_length=128)
    transcription = models.TextField(_('Аудиотранскрибция'))

    class Meta:
        verbose_name = _('История запросов к Whisper')
        verbose_name_plural = _('История запросов к Whisper')
        ordering = ('created_at',)

    def __str__(self):
        return f'User: {self.user}, File ID: {self.file_id}'


class HistoryTranslation(Create):
    """
    Модель для хранения истории переводов.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с историей переводов.
    - message (`TextField`): Исходное сообщение.
    - translation (`TextField`): Перевод сообщения.

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history_translation')
    message = models.TextField(_('Сообщение'))
    translation = models.TextField(_('Перевод'))

    class Meta:
        verbose_name = _('История запросов для перевода')
        verbose_name_plural = _('История запросов для перевода')
        ordering = ('created_at',)

    def __str__(self):
        return f'User: {self.user}, Message: {self.message}'
