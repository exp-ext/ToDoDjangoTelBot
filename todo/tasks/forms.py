from core.widget import MinimalSplitDateTimeMultiWidget
from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    server_datetime = forms.DateTimeField(
        label='Дата и время мероприятия',
        help_text='Для ДР время можно оставить пустым',
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
            'text',
            'reminder_period',
            'it_birthday',
            'remind_min'
        )

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        user = kwargs.pop('initial').get('user')
        self.fields['group'] = forms.ModelChoiceField(
            queryset=user.groups_connections.all()
        )
        self.fields['group'].required = False
        self.fields['group'].label = (
            'Место вывода сообщений о напоминании.'
        )
        self.fields['group'].help_text = (
            '<p style="color: #82818a;"> Оповещение придёт в личный чат, '
            'если оставить поле пустым.<br>'
            'Для появление Вашей группы в выпадающем списке, необходимо '
            'в её чате хотя бы один раз вызвать меню.</p>'
        )
