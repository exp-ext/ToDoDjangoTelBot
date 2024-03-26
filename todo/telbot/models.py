from core.models import Create
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserPrompt(models.Model):
    """
    Модель для хранения промптов, используемых с моделями GPT.

    ### Fields:
    - title (`CharField`): Название промпта.
    - prompt_text (`TextField`): Текст промпта.
    - default (`BooleanField`): Флаг установки промпта по умолчанию.

    ### Methods:
    - clean(*args, **kwargs): Проверяет корректность параметров модели перед сохранением.
    - save(*args, **kwargs): Переопределенный метод сохранения объекта модели для выполнения предварительной проверки перед сохранением.

    """
    title = models.CharField(_('название промпта'), max_length=28)
    prompt_text = models.TextField(_('текст промпта'))
    default = models.BooleanField(_('по умолчанию'), default=False)

    class Meta:
        verbose_name = _('промпт для GPT')
        verbose_name_plural = _('промпты для GPT')

    def __str__(self):
        return self.title

    def clean(self, *args, **kwargs):
        is_there_default_model = UserPrompt.objects.filter(default=True).exclude(pk=self.pk).exists()
        if not self.default and not is_there_default_model:
            raise ValidationError('Необходимо указать хотя бы один промпт по умолчанию.')
        if self.default and is_there_default_model:
            raise ValidationError('По умолчанию может быть только один промпт.')

    def save(self, *args, **kwargs):
        self.clean()
        super(UserPrompt, self).save(*args, **kwargs)


class GptModels(models.Model):
    """
    Модель для хранения параметров моделей GPT.

    ### Fields:
    - title (`CharField`): Название модели GPT.
    - default (`BooleanField`): Флаг доступности модели всем по умолчанию.
    - token (`CharField`): Токен для запроса к модели.
    - context_window (`IntegerField`): Окно количества токенов для передачи истории в запросе.
    - max_request_token (`IntegerField`): Максимальное количество токенов в запросе.
    - time_window (`IntegerField`): Окно времени для передачи истории в запросе, в минутах (по умолчанию 30).

    ### Methods:
    - clean(*args, **kwargs): Проверяет корректность параметров модели перед сохранением.
    - save(*args, **kwargs): Переопределенный метод сохранения объекта модели для выполнения предварительной проверки перед сохранением.

    """
    title = models.CharField(_('модель GPT'), max_length=28)
    default = models.BooleanField(_('доступна всем по умолчанию'), default=False)
    token = models.CharField(_('токен для запроса'), max_length=51)
    context_window = models.IntegerField(_('окно количества токенов для передачи истории в запросе'))
    max_request_token = models.IntegerField(_('максимальное количество токенов в запросе'))
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
    """
    Модель для хранения разрешенных GPT моделей для пользователя.

    ### Fields:
    - user (`OneToOneField`): Пользователь, которому принадлежат модели.
    - active_model (`ForeignKey`, опционально): Активная модель для пользователя.
    - approved_models (`ManyToManyField`): Разрешенные модели для пользователя.
    - time_start (`DateTimeField`): Время начала окна для передачи истории.
    - active_prompt (`ForeignKey`, опционально): Активный промпт для пользователя.

    ### Methods:
    - save(*args, **kwargs): Переопределенный метод сохранения объекта модели для автоматического назначения активной модели при создании нового объекта.

    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='approved_models')
    active_model = models.ForeignKey(GptModels, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_for_users', verbose_name=_('активная модель'))
    approved_models = models.ManyToManyField(to=GptModels, related_name='approved_users')
    time_start = models.DateTimeField(_('время начала окна для передачи истории'), default=now)
    active_prompt = models.ForeignKey(UserPrompt, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_for_user', verbose_name=_('активный промпт'))

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

        if not self.active_prompt:
            default_prompt = UserPrompt.objects.filter(default=True).first()
            if default_prompt:
                self.active_prompt = default_prompt
                self.save(update_fields=['active_prompt'])

        if is_new and default_model:
            if not self.approved_models.filter(id=default_model.id).exists():
                self.approved_models.add(default_model)


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
