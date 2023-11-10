from bs4 import BeautifulSoup
from django import forms
from django.forms import Textarea
from users.models import Group

from .models import Comment, Post, PostContents


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

    def clean_text(self) -> str:
        text = self.cleaned_data["text"]
        soup = BeautifulSoup(text, features="html.parser")
        current_node_db = None

        if self.instance:
            self.instance.contents.all().delete()

        contents = []

        for tag in soup.find_all(['h2', 'h4']):
            if tag.name == 'h2':
                text = text.replace(str(tag), f'<section id="{tag.text}">{str(tag)}</section>')
                current_node_db = PostContents.objects.create(post=self.instance, anchor=tag.text, is_root=True)
            elif tag.name == 'h4':
                text = text.replace(str(tag), f'<section id="{tag.text}">{str(tag)}</section>')
                contents.append(
                    PostContents(
                        post=self.instance,
                        anchor=tag.text,
                        parent=current_node_db,
                        is_root=True,
                    )
                )

        if contents:
            PostContents.objects.bulk_create(contents)
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'rows': 2, 'cols': 10}),
        }
