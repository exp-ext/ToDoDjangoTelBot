from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created_at', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('created_at',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'
