from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe

from .models import (GptModels, HistoryAI, HistoryDALLE, ReminderAI,
                     UserGptModels)

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


@admin.register(ReminderAI)
class ReminderAIAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'question_tokens', 'answer_tokens')
    fieldsets = (
        ('Основные данные', {'fields': ('user', 'question_tokens', 'answer_tokens')}),
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
        ('Картинка', {'fields': ('preview',)}),
    )
    search_fields = ('answer',)
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        ('user__first_name', admin.AllValuesFieldListFilter),
    )

    readonly_fields = ('preview',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            full_name=Concat('user__first_name', Value(' '), 'user__last_name')
        )
        return queryset

    def full_name(self, obj):
        return obj.user.get_full_name()

    full_name.short_description = 'Full Name'

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.answer.get("media")}" style="max-height: 800px;">'
        )


@admin.register(GptModels)
class GptModelsAdmin(admin.ModelAdmin):
    pass


class GptModelsInline(admin.StackedInline):
    model = GptModels.approved_users.through
    extra = 0


@admin.register(UserGptModels)
class GptModelsAdmin(admin.ModelAdmin):
    inlines = (GptModelsInline,)
