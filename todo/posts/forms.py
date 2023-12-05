from bs4 import BeautifulSoup
from django import forms
from django.forms import Textarea
from users.models import Group

from .models import Comment, Post


class GroupMailingForm(forms.Form):
    forismatic_quotes = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((False, 'Выключена'), (True, 'Включена')),
        widget=forms.RadioSelect(
            attrs={'onchange': 'form.submit()'}
        )
    )


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'group', 'text', 'image')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        user = kwargs.pop('initial').get('user')
        user_groups = user.groups_connections.values_list('group', flat=True)
        self.fields['group'] = forms.ModelChoiceField(
            queryset=Group.objects.filter(id__in=user_groups)
        )
        self.fields['group'].required = False
        self.fields['group'].label = 'Группа, к которой будет относиться пост'

    def clean_title(self) -> str:
        title = self.cleaned_data.get('title')
        if not title or len(title) >= 80:
            raise forms.ValidationError('Запрещено создавать пост без заголовка или с его длинной более 80 символов.')
        this_post_id = self.instance.id if self.instance else None
        if Post.objects.filter(title=title).exclude(id=this_post_id).exists():
            raise forms.ValidationError('Найден очень похожий заголовок поста.')
        return title

    def clean_text(self) -> str:
        text = self.cleaned_data.get('text')
        soup = BeautifulSoup(text, features="html.parser")

        for tag in soup.find_all(['h2', 'h4']):
            if len(tag.string) > 70:
                raise forms.ValidationError('Теги h2 и h4 не могут быть более 70 символов.')
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'rows': 2, 'cols': 10}),
        }
