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
        'text',
        'remind_at',
        'reminder_period',
        'it_birthday'
    )
    search_fields = ('text',)
    list_filter = ('group', 'user')
    empty_value_display = '-пусто-'
