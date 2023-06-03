from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import HistoryAI, HistoryDALLE

User = get_user_model()


@admin.register(HistoryAI)
class HistoryAIAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at',)
    fieldsets = (
        ('Основные данные', {
            'fields': (
                'user', 'question_tokens', 'answer_tokens'
            )
        }),
        ('Диалог', {'fields': ('question', 'answer')}),
    )
    search_fields = ('answer',)
    list_filter = ('user', 'user__first_name')


@admin.register(HistoryDALLE)
class HistoryDALLEAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    fieldsets = (
        ('Основные данные', {
            'fields': ('user',)
        }),
        ('Диалог', {'fields': ('question', 'answer')}),
    )
    search_fields = ('answer',)
    list_filter = ('user', 'user__first_name')
