# from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
        labels = {
            'username': ('Your Telegram ID'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = (
            'Ваш телеграмм ID. Получить его можно в чате с ботом.'
        )
        self.fields['username'].widget.attrs['readonly'] = True
