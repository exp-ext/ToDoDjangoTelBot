from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Comment, Post, PostContents, PostTags


class TreePostContentsAdmin(TreeAdmin):
    form = movenodeform_factory(PostContents)


admin.site.register(PostContents, TreePostContentsAdmin)


class PostTargetInline(admin.StackedInline):
    model = PostTags.posts.through
    extra = 0
    classes = ('collapse',)

    class Meta:
        verbose_name = _('тег')
        verbose_name_plural = _('теги')


class PostContentsAdminInline(admin.StackedInline):
    model = PostContents
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'author', 'group', 'moderation')
    search_fields = ('text',)
    list_filter = ('created_at', 'author',)
    list_editable = ('group', 'moderation')
    empty_value_display = '-пусто-'

    inlines = (PostTargetInline, PostContentsAdminInline)
    fieldsets = (
        ('Главное', {'fields': ('title', 'author', 'group')}),
        ('Текст', {'fields': ('text',)}),
        ('Модерация', {'fields': ('moderation',)}),
        ('Картинка', {'fields': ('image', 'preview')}),
    )
    empty_value_display = '-пусто-'
    inlines = (PostTargetInline,)
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" style="max-height: 200px;">')


@admin.register(PostTags)
class PostTagsAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass
