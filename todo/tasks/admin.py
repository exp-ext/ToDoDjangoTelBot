from django.contrib import admin

from .models import CelebratoryFriend, Task, WishList


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    pass


@admin.register(CelebratoryFriend)
class CelebratoryFriendAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'group',
        'remind_at',
        'reminder_period',
    )
    search_fields = ('user',)
    list_filter = ('group', 'user')
    empty_value_display = '-пусто-'
