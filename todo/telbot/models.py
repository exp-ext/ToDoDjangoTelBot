from asgiref.sync import sync_to_async
from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.manager import BaseManager

User = get_user_model()


class AsyncManager(BaseManager.from_queryset(models.QuerySet)):
    """
    Менеджер модели, который добавляет поддержку асинхронных
    операций с базой данных.
    """


class HistoryAI(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='history_ai'
    )
    question = models.TextField(
        verbose_name='Вопрос'
    )
    answer = models.TextField(
        verbose_name='Ответ'
    )

    class Meta:
        verbose_name = 'История запросов к ИИ'
        verbose_name_plural = 'История запросов к ИИ'
        ordering = ('created_at',)

    def __str__(self):
        return self.question

    @sync_to_async
    def save(self, *args, **kwargs):
        """
        Переопределение метода save() для поддержки асинхронного
        сохранения объекта в базе данных.
        """
        return super().save(*args, **kwargs)


class HistoryDALLE(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='history_dalle'
    )
    question = models.TextField(
        verbose_name='Запрос'
    )
    answer = models.JSONField(
        verbose_name='Ответ'
    )

    class Meta:
        verbose_name = 'История запросов к Dalle'
        verbose_name_plural = 'История запросов к Dalle'
        ordering = ('created_at',)

    def __str__(self):
        return self.question


class HistoryWhisper(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='history_whisper'
    )
    file_id = models.CharField(
        max_length=128,
        verbose_name='Id файла'
    )
    transcription = models.TextField(
        verbose_name='Аудиотранскрибция'
    )

    class Meta:
        verbose_name = 'История запросов к Whisper'
        verbose_name_plural = 'История запросов к Whisper'
        ordering = ('created_at',)

    def __str__(self):
        return self.transcription


class HistoryTranslation(Create):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='history_translation'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    translation = models.TextField(
        verbose_name='Перевод'
    )

    class Meta:
        verbose_name = 'История запросов для перевода'
        verbose_name_plural = 'История запросов для перевода'
        ordering = ('created_at',)

    def __str__(self):
        return self.message
