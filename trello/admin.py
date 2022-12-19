from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Card, Column, MainDesk, Comment, MemberDesk, CheckList, Metki, MainDeskFavorites, MainDeskArchive


class CustomUserAdmin(UserAdmin):
    Model = CustomUser
    list_display = ["username", "email"]


admin.site.register(MainDesk)
admin.site.register(Column)
admin.site.register(Card)
admin.site.register(Comment)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MemberDesk)
admin.site.register(CheckList)
admin.site.register(Metki)
admin.site.register(MainDeskFavorites)
admin.site.register(MainDeskArchive)