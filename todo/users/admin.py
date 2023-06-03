from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from .models import Group, GroupConnections, Location

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
        'role',
        'favorite_group'
    )
    fieldsets = (
        ('Данные пользователя', {
            'fields': ('username', 'first_name', 'last_name')
        }),
        ('Аватар', {'fields': ('image', 'preview')}),
        ('Категория и статус', {
            'fields': ('is_active', 'is_staff', 'role', 'is_superuser')
        }),
        ('Группы и связи', {'fields': ('favorite_group',)}),
    )
    inlines = (GroupConnectionsInline, UserLocationInline)
    search_fields = ('last_name',)
    list_filter = ('favorite_group',)
    readonly_fields = ('preview',)
    empty_value_display = '-пусто-'

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'title', 'slug')
    fieldsets = (
        ('Основные данные', {'fields': ('title', 'chat_id', 'description')}),
        ('Логотип_группы', {'fields': ('image', 'preview')}),
        ('Ссылки', {'fields': ('slug', 'link')}),
    )
    inlines = (GroupConnectionsInline,)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )
