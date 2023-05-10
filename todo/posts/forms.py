from django import forms
from django.forms import Textarea
from django.shortcuts import get_object_or_404
from users.models import Group

from .models import Comment, Post


class GroupMailingForm(forms.Form):
    forismatic_quotes = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((False, 'Выключена'), (True, 'Включена')),
        widget=forms.RadioSelect(
            attrs={'onchange': 'form.submit();'}
        )
    )


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'group', 'text', 'image')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        user = kwargs.pop('initial').get('user')
        self.fields['group'] = forms.ModelChoiceField(
            queryset=user.groups_connections.all()
        )
        self.fields['group'].required = False
        self.fields['group'].label = (
            'Группа, к которой будет относиться пост'
        )

    def clean_group(self):
        group = self.cleaned_data['group']
        if group:
            return get_object_or_404(Group, pk=group.group_id)
        return group


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'rows': 2, 'cols': 10}),
        }
