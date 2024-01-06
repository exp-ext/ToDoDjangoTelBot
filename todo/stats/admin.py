from django.contrib import admin
from stats.models import BlockListIP, PostsCounter


@admin.register(PostsCounter)
class PartnerBannerAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'ref_url',
        'ip',
        'block_list',
        'browser',
        'is_bot',
        'is_mobile',
        'is_pc',
        'is_tablet',
        'is_touch_capable',
    )
    list_editable = ('block_list', )

    fieldsets = (
        ('Пост', {'fields': ('post', )}),
        ('Система', {'fields': ('browser', 'os',)}),
        ('Сущность', {'fields': ('is_bot', 'is_mobile', 'is_pc', 'is_tablet', 'is_touch_capable')}),
    )

    search_fields = ('browser', 'os', )
    list_filter = (
        'post',
        'block_list',
        'browser',
        ('created_at', admin.DateFieldListFilter),
        ('is_bot', admin.BooleanFieldListFilter),
        ('is_mobile', admin.BooleanFieldListFilter),
        ('is_pc', admin.BooleanFieldListFilter),
        ('is_tablet', admin.BooleanFieldListFilter),
        ('is_touch_capable', admin.BooleanFieldListFilter),
    )


@admin.register(BlockListIP)
class BlockListIPAdmin(admin.ModelAdmin):
    list_display = (
        'ip',
        'block_list',
    )
    list_editable = ('block_list',)
    search_fields = ('ip', )
    list_filter = (
        'ip',
        ('created_at', admin.DateFieldListFilter),
        ('block_list', admin.BooleanFieldListFilter),
    )
