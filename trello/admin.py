from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Card, Column, MainDesk, Comment, MemberDesk, CheckList, Metki, MainDeskFavorites, MainDeskArchive


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'auth_provider', 'created_at']


admin.site.register(MainDesk)
admin.site.register(Column)
admin.site.register(Card)
admin.site.register(Comment)
admin.site.register(User, UserAdmin)
admin.site.register(MemberDesk)
admin.site.register(CheckList)
admin.site.register(Metki)
admin.site.register(MainDeskFavorites)
admin.site.register(MainDeskArchive)