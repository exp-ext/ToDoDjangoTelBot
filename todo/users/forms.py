from django import forms
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Group

User = get_user_model()


class MyDateInput(forms.DateInput):
    input_type = 'date'
    format = '%Y-%m-%d'


class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        label='Номер телефона',
        widget=forms.TextInput(
            attrs={
                'id': "phone_number",
                'placeholder': "+7(___)___-__-__",
            }
        ),
        required=False,
    )
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
            'tg_id',
            'username',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'favorite_group',
            'birthday',
        )
        widgets = {
            'image': forms.FileInput(
                attrs={'onchange': 'form.submit()'}
            )
        }
        labels = {
            'username': 'Имя пользователя',
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['tg_id'].widget.attrs['readonly'] = True
        user = kwargs.get('instance')
        self.fields['favorite_group'] = forms.ModelChoiceField(
            queryset=user.groups_connections.all()
        )
        self.fields['favorite_group'].required = False
        self.fields['favorite_group'].label = (
            'Группа по умолчанию для действий без выбора группы'
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
        if image.size > 10000000:
            raise forms.ValidationError(
                "Размер вашего фото превышает разрешенный в 1мб."
            )
        return image
