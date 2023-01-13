from django import forms
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from users.models import Group

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
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].help_text = (
            'Ваш телеграмм ID. Получить его можно в чате с ботом.'
        )
        user = kwargs.get('instance')
        self.fields['favorite_group'] = forms.ModelChoiceField(
            queryset=user.groups_connections.all()
        )
        self.fields['favorite_group'].required = False
        self.fields['favorite_group'].label = (
            'Группа которая будет назначена основной для аккаунта.'
        )

    def clean_favorite_group(self):
        favorite_group = self.cleaned_data['favorite_group']
        if favorite_group:
            return get_object_or_404(Group, pk=favorite_group.group_id)
        return favorite_group

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            raise forms.ValidationError("No image!")
        if image.size > 1000000:
            raise forms.ValidationError(
                "Размер вашего фото превышает разрешенный в 1мб."
            )
        return image
