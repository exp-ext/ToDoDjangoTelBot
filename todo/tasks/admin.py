from django.contrib import admin

from .models import CelebratoryFriend, Task, WishList


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    pass


@admin.register(CelebratoryFriend)
class CelebratoryFriendAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskFriendAdmin(admin.ModelAdmin):
    pass
