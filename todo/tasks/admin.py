from django.contrib import admin
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
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
    list_filter = (
        ('remind_at', admin.DateFieldListFilter),
        'group',
        ('user__first_name', admin.AllValuesFieldListFilter),
    )
    empty_value_display = '-пусто-'
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.picture_link}" style="max-height: 200px;">'
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            full_name=Concat('user__first_name', Value(' '), 'user__last_name')
        )
        return queryset

    def full_name(self, obj):
        return obj.user.get_full_name()

    full_name.short_description = 'Full Name'
