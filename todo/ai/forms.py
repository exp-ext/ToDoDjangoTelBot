from django import forms
from telbot.models import GptModels, UserGptModels, UserPrompt


class UserGptModelsForm(forms.ModelForm):
    active_prompt = forms.ModelChoiceField(queryset=UserPrompt.objects.all(), required=False, label='Активный промпт')

    class Meta:
        model = UserGptModels
        fields = ('active_model', 'active_prompt')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super(UserGptModelsForm, self).__init__(*args, **kwargs)
        if instance:
            self.fields['active_model'].queryset = instance.approved_models.all()

    def clean_active_model(self):
        active_model = self.cleaned_data.get('active_model')
        if not active_model:
            active_model = GptModels.objects.filter(default=True).first()
            if not active_model:
                raise forms.ValidationError("Активная модель не выбрана и отсутствует по умолчанию.")
        return active_model

    def clean_active_prompt(self):
        active_prompt = self.cleaned_data.get('active_prompt')
        if not active_prompt:
            active_prompt = UserPrompt.objects.filter(default=True).first()
            if not active_prompt:
                raise forms.ValidationError("Активный промпт не выбран и отсутствует по умолчанию.")
        return active_prompt
