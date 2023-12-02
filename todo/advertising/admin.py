from advertising.models import AdvertisementWidget, PartnerBanner, TelegramMailing
from django.contrib import admin
from django.utils.safestring import mark_safe


@admin.register(PartnerBanner)
class PartnerBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'reference')
    fieldsets = (
        ('Данные не для представления на сайте', {'fields': ('created_at', 'title',)}),
        ('Картинка баннера', {'fields': ('image', 'preview')}),
        ('Ссылка', {'fields': ('reference',)}),
        ('Текст', {'fields': ('text',)}),
    )
    readonly_fields = ('preview', 'created_at')

    def preview(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" style="max-height: 200px;">')


@admin.register(TelegramMailing)
class TelegramMailingAdmin(admin.ModelAdmin):
    list_display = ('title', 'remind_at')
    fieldsets = (
        ('Данные не для представления на сайте', {'fields': ('created_at', 'title',)}),
        ('Картинка баннера', {'fields': ('image', 'image_full_url', 'preview')}),
        ('Ссылка', {'fields': ('reference',)}),
        ('Текст', {'fields': ('text',)}),
        ('Получатели', {'fields': ('target', 'remind_at')}),
    )
    readonly_fields = ('preview', 'created_at', 'image_full_url')

    def preview(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" style="max-height: 200px;">')

    def image_full_url(self, obj):
        absolute_image_url = self.request.build_absolute_uri(obj.image.url)
        return mark_safe(f'<a href="{absolute_image_url}">{absolute_image_url}</a>')

    def get_fieldsets(self, request, obj=None):
        self.request = request
        return super().get_fieldsets(request, obj)


@admin.register(AdvertisementWidget)
class PartnerBannerAdmin(admin.ModelAdmin):
    list_display = ('advertiser', 'title', 'created_at')
    fieldsets = (
        ('Данные не для представления на сайте', {'fields': ('created_at', 'title', 'advertiser')}),
        ('Тип расположения', {'fields': ('form',)}),
        ('Текст', {'fields': ('script',)}),
    )
    readonly_fields = ('created_at',)
