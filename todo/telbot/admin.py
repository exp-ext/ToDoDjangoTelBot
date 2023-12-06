from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Value
from django.db.models.functions import Concat

from .models import HistoryAI, HistoryDALLE, HistoryWhisper

User = get_user_model()


@admin.register(HistoryAI)
class HistoryAIAdmin(admin.ModelAdmin):
    list_display = ('user', 'room_group_name', 'created_at', 'question_tokens', 'answer_tokens')
    fieldsets = (
        ('Основные данные', {'fields': ('user', 'room_group_name', 'question_tokens', 'answer_tokens')}),
        ('Диалог', {'fields': ('question', 'answer')}),
    )
    search_fields = ('answer',)
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        ('user__first_name', admin.AllValuesFieldListFilter),
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


@admin.register(HistoryDALLE)
class HistoryDALLEAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'created_at')
    fieldsets = (
        ('Основные данные', {'fields': ('user',)}),
        ('Диалог', {'fields': ('question', 'answer')}),
    )
    search_fields = ('answer',)
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        ('user__first_name', admin.AllValuesFieldListFilter),
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


@admin.register(HistoryWhisper)
class HistoryWhisperAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'created_at')
    fieldsets = (
        ('Основные данные', {'fields': ('user',)}),
        ('Диалог', {'fields': ('file_id', 'transcription')}),
    )
    search_fields = ('transcription',)
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        ('user__first_name', admin.AllValuesFieldListFilter),
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
