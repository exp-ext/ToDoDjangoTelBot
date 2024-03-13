from asgiref.sync import sync_to_async
from core.models import Create
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.manager import BaseManager
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class GptModels(models.Model):
    title = models.CharField(_('модель GPT'), max_length=28)
    default = models.BooleanField(_('доступна всем по умолчанию'), default=False)
    token = models.CharField(_('токен для запроса'), max_length=51)
    context_window = models.IntegerField(_('окно токенов для передачи истории в запросе'))
    max_request_token = models.IntegerField(_('максимальное количество токенов в запросе пользователя'))
    time_window = models.IntegerField(_('окно времени для передачи истории в запросе, мин'), default=30)

    class Meta:
        verbose_name = _('модель GPT OpenAi')
        verbose_name_plural = _('модели GPT OpenAi')

    def __str__(self):
        return self.title

    def clean(self, *args, **kwargs):
        is_there_default_model = GptModels.objects.filter(default=True).exclude(pk=self.pk).exists()
        if not self.default and not is_there_default_model:
            raise ValidationError('Необходимо указать хотя бы одну модель по умолчанию для всех.')
        if self.default and is_there_default_model:
            raise ValidationError('По умолчанию может быть только одна модель.')

    def save(self, *args, **kwargs):
        self.clean()
        super(GptModels, self).save(*args, **kwargs)


class UserGptModels(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='approved_models')
    active_model = models.ForeignKey(GptModels, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_for_users', verbose_name=_('Активная модель'))
    approved_models = models.ManyToManyField(to=GptModels, related_name='approved_users')
    time_start = models.DateTimeField(_('время начала окна для передачи истории'), default=now)

    class Meta:
        verbose_name = _('разрешенная GPT модели юзера')
        verbose_name_plural = _('разрешенные GPT модели юзера')

    def __str__(self):
        return f'User: {self.user}, Active model: {self.active_model}'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super(UserGptModels, self).save(*args, **kwargs)

        if not self.active_model:
            default_model = GptModels.objects.filter(default=True).first()
            if default_model:
                self.active_model = default_model
                self.save(update_fields=['active_model'])

        if is_new and default_model:
            if not self.approved_models.filter(id=default_model.id).exists():
                self.approved_models.add(default_model)


class AsyncManager(BaseManager.from_queryset(models.QuerySet)):
    """
    Менеджер модели, который добавляет поддержку асинхронных операций с базой данных.
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
        Переопределение метода save() для поддержки асинхронного сохранения объекта в базе данных.
        """
        return super().save(*args, **kwargs)


class ReminderAI(Create):
    """
    Модель для хранения истории вопросов и ответов AI.

    ### Fields:
    - user (`ForeignKey`): Пользователь, связанный с историей.
    - question (`TextField`): Вопрос, заданный пользователем.
    - question_tokens (`PositiveIntegerField`): Количество токенов в вопросе (может быть null).
    - answer (`TextField`): Ответ, сгенерированный AI.
    - answer_tokens (`PositiveIntegerField`): Количество токенов в ответе (может быть null).

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminder_history_ai', null=True, blank=True)
    question = models.TextField(_('Вопрос'))
    question_tokens = models.PositiveIntegerField(null=True)
    answer = models.TextField(_('Ответ'))
    answer_tokens = models.PositiveIntegerField(null=True)

    class Meta:
        verbose_name = _('История запросов на преобразования напоминания к ИИ')
        verbose_name_plural = _('История запросов на преобразования напоминания к ИИ')
        ordering = ('created_at',)

    def __str__(self):
        return f'User: {self.user}, Question: {self.question}'

    @sync_to_async
    def save(self, *args, **kwargs):
        """
        Переопределение метода save() для поддержки асинхронного сохранения объекта в базе данных.
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

    @sync_to_async
    def save(self, *args, **kwargs):
        """
        Переопределение метода save() для поддержки асинхронного сохранения объекта в базе данных.
        """
        return super().save(*args, **kwargs)


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
