from django.contrib import admin
from stats.models import PostsCounter


@admin.register(PostsCounter)
class PartnerBannerAdmin(admin.ModelAdmin):
    pass
