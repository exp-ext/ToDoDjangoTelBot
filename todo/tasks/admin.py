from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'group',
        'remind_at',
        'reminder_period',
    )
    fieldsets = (
        ('Создано:', {
            'fields': ('user', 'group')
        }),
        ('Напоминание на:', {
            'fields': (
                'server_datetime', 'remind_min', 'remind_at', 'reminder_period'
            )
        }),
        ('Напоминание', {
            'fields': ('text',)
        }),
        ('Картинка в сообщении', {'fields': ('picture_link', 'preview')}),
    )
    search_fields = ('user',)
    list_filter = ('group', 'user')
    empty_value_display = '-пусто-'
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.picture_link}" style="max-height: 200px;">'
        )
