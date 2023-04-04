from core.models import Create
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


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
