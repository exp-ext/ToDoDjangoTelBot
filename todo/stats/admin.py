from django.contrib import admin
from stats.models import PostsCounter


@admin.register(PostsCounter)
class PartnerBannerAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'browser',
        'is_bot',
        'is_mobile',
        'is_pc',
        'is_tablet',
        'is_touch_capable',
    )

    fieldsets = (
        ('Пост', {'fields': ('post', )}),
        ('Система', {'fields': ('browser', 'os',)}),
        ('Сущность', {'fields': ('is_bot', 'is_mobile', 'is_pc', 'is_tablet', 'is_touch_capable')}),
    )

    search_fields = ('browser', 'os', )
    list_filter = (
        'post',
        'browser',
        ('created_at', admin.DateFieldListFilter),
        ('is_bot', admin.BooleanFieldListFilter),
        ('is_mobile', admin.BooleanFieldListFilter),
        ('is_pc', admin.BooleanFieldListFilter),
        ('is_tablet', admin.BooleanFieldListFilter),
        ('is_touch_capable', admin.BooleanFieldListFilter),
    )
