from django import forms
from django.contrib.auth import get_user_model

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
        )
    )
    birthday = forms.DateField(
        widget=MyDateInput(),
    )

    class Meta:
        model = User
        fields = (
            'image',
            'first_name',
            'last_name',
            'username',
            'email',
            'favorite_group',
            'birthday',
        )
        labels = {
            'username': ('Your Telegram ID'),
            'birthday': ('Date Of Birth'),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].help_text = (
            'Ваш телеграмм ID. Получить его можно в чате с ботом.'
        )
