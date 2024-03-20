from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from .models import Group, GroupConnections, GroupMailing, Location

User = get_user_model()


class GroupConnectionsInline(admin.TabularInline):
    model = GroupConnections
    extra = 0
    verbose_name = 'Привязанная группа'
    verbose_name_plural = 'Привязанные группы'


class UserLocationInline(admin.TabularInline):
    model = Location
    extra = 0
    verbose_name = 'Последнее местонахождение'
    verbose_name_plural = 'Последнее местонахождение'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'favorite_group',
        'is_blocked_bot',
    )
    fieldsets = (
        ('Данные пользователя', {'fields': ('tg_id', 'username', 'first_name', 'last_name')}),
        ('Аватар', {'fields': ('image', 'preview')}),
        ('Категория и статус', {'fields': ('is_active', 'is_staff', 'role', 'is_superuser')}),
        ('Контакты', {'fields': ('phone_number', 'email',)}),
        ('Группы и связи', {'fields': ('favorite_group',)}),
    )
    inlines = (GroupConnectionsInline, UserLocationInline)
    search_fields = ('last_name', 'phone_number', 'email')
    list_filter = (
        ('is_staff', admin.BooleanFieldListFilter),
        ('last_login', admin.DateFieldListFilter),
    )
    list_editable = ('is_blocked_bot',)
    readonly_fields = ('preview',)
    empty_value_display = '-пусто-'

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )


class GroupMailingInline(admin.TabularInline):
    model = GroupMailing
    extra = 0
    verbose_name = 'Рассылка для группы'
    verbose_name_plural = 'Рассылки для групп'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'title', 'slug')
    fieldsets = (
        ('Основные данные', {'fields': ('title', 'chat_id', 'description')}),
        ('Логотип_группы', {'fields': ('image', 'preview')}),
        ('Ссылки', {'fields': ('slug', 'link')}),
    )
    inlines = (GroupConnectionsInline, GroupMailingInline)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )
