from datetime import datetime, timedelta

import pytz
from core.views import similarity
from core.widget import MinimalSplitDateTimeMultiWidget
from django import forms
from django.core.exceptions import ValidationError
from users.models import Group

from .models import Task


class TaskForm(forms.ModelForm):
    server_datetime = forms.DateTimeField(
        label='Дата и время мероприятия',
        widget=MinimalSplitDateTimeMultiWidget()
    )
    it_birthday = forms.BooleanField(
        label='День рождения?',
        initial=False,
        required=False,
        widget=forms.CheckboxInput(
            attrs={'style': 'width:25px;height:25px;'}
        )
    )
    tz = forms.CharField(
        label='Часовой пояс',
        required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        )
    )

    class Meta:
        model = Task
        fields = (
            'group',
            'server_datetime',
            'picture_link',
            'image',
            'text',
            'reminder_period',
            'it_birthday',
            'remind_min'
        )

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        user = kwargs.pop('initial').get('user')
        user_groups = user.groups_connections.values_list('group', flat=True)
        self.fields['group'] = forms.ModelChoiceField(
            queryset=Group.objects.filter(id__in=user_groups)
        )
        self.fields['group'].required = False
        self.fields['group'].label = 'Место вывода сообщений о напоминании.'
        self.fields['group'].help_text = (
            '<p style="color: #82818a;"> Оповещение придёт в личный чат, '
            'если оставить поле пустым.<br>'
            'Для появление Вашей группы в выпадающем списке, необходимо '
            'в её чате хотя бы один раз вызвать меню.</p>'
        )

    def clean_server_datetime(self):
        server_datetime = self.cleaned_data['server_datetime']
        user_tz = self.initial.get('tz')
        tz = pytz.timezone(user_tz)
        if server_datetime <= datetime.now(tz):
            raise ValidationError('Назначенное время не может быть меньше текущего.')
        return server_datetime

    def clean_text(self):
        text = self.cleaned_data['text']
        if self.initial.get('is_edit'):
            return text
        group = self.cleaned_data['group']
        server_datetime = self.cleaned_data['server_datetime']
        user = self.initial.get('user')

        start_datetime = server_datetime - timedelta(minutes=60)
        end_datetime = server_datetime + timedelta(minutes=60)

        if group:
            tasks = group.tasks.filter(
                server_datetime__range=[start_datetime, end_datetime],
                group=group
            )
        else:
            tasks = user.tasks.filter(server_datetime__range=[start_datetime, end_datetime])
        for task in tasks:
            simile = similarity(task.text, text)
            if simile > 0.62:
                raise ValidationError('Очень похожая запись уже присутствует в напоминаниях.')
        return text
