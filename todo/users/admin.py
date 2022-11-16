from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Group, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'is_admin')
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height: 200px;">'
        )
