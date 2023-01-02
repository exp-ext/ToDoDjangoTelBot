from core.widget import MinimalSplitDateTimeMultiWidget
from django import forms
from django.contrib.auth import get_user_model

from .models import Task

User = get_user_model()


class MyDateInput(forms.DateInput):
    input_type = 'date'
    format = '%Y-%m-%d'


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                'id': "email",
                'placeholder': "name@domen.info",
            }
        ),
        required=False,
    )
    birthday = forms.DateField(
        label='День рождения',
        widget=MyDateInput(),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            'image',
            'username',
            'first_name',
            'last_name',
            'email',
            'favorite_group',
            'birthday',
        )
        widgets = {
            'image': forms.FileInput(attrs={
                'onchange': "form.submit()"
            })
        }
        labels = {
            'username': 'Your Telegram ID',
            'favorite_group': 'Группа фаворит',
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].help_text = (
            'Ваш телеграмм ID. Получить его можно в чате с ботом.'
        )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            raise forms.ValidationError("No image!")
        if image.size > 1000000:
            raise forms.ValidationError(
                "Размер вашего фото превышает разрешенный в 1мб."
            )
        return image


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
            'Группа для вывода напоминания.'
        )
        self.fields['group'].help_text = (
            'Оповещение придёт в личный чат, если оставить пустым.'
        )
