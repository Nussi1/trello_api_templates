from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date
from config import settings
from django.contrib.auth.models import AbstractUser
from django_resized import ResizedImageField
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)

from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

class UserManager(BaseUserManager):

    def create_user(self, username, email, password=None):
        if username is None:
            raise TypeError('Users should have a username')
        if email is None:
            raise TypeError('Users should have a Email')

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password=None):
        if password is None:
            raise TypeError('Password should not be none')

        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


AUTH_PROVIDERS = {'facebook': 'facebook', 'google': 'google',
                  'twitter': 'twitter', 'email': 'email'}


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(
        max_length=255, blank=False,
        null=False, default=AUTH_PROVIDERS.get('email'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }


# class CustomUser(AbstractUser):
#     email = models.EmailField(unique=True)
#
#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ("username", )
#
#     def __str__(self):
#         return self.username


class MemberDesk(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    desk = models.ForeignKey('MainDesk', on_delete=models.CASCADE, null=True, related_name='members')

    def __str__(self):
        return str(self.user)

class MainDesk(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    created_date = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    image = ResizedImageField(upload_to='images/', quality=85)

    def __str__(self):
        return self.title


class MainDeskArchive(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='archives')
    desk = models.ForeignKey('MainDesk', on_delete=models.CASCADE, null=True)


class MainDeskFavorites(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    desk = models.ForeignKey('MainDesk', on_delete=models.CASCADE)


class CardSearch(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='searches')
    label = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='label')


class Column(models.Model):
    desk = models.ForeignKey('MainDesk', on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=30)

    class Meta:
        verbose_name = 'Column'
        verbose_name_plural = 'Columns'

    def __str__(self):
        return self.title


class Card(models.Model):
    column = models.ForeignKey('Column', on_delete=models.CASCADE, related_name="entries")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    content = models.CharField(max_length=500)
    date_created = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(null=True)
    CHOICES = (
        ('red', 'red'),
        ('blue', 'blue'),
        ('green', 'green'),
        ('yellow', 'yellow')
    )
    choice = models.CharField(max_length=255, choices=CHOICES)
    docfile = models.FileField(upload_to='documents/%Y/%m/%d', blank=True)


    def __str__(self):
        return self.title

    @property
    def Days_till(self):
        today = date.today()
        days_till = self.deadline.date() - today
        return days_till

    class Meta:
        verbose_name_plural = "Entries"


class Comment(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    body = models.CharField(max_length=300)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    entry = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='comments')


class CheckList(models.Model):
    title = models.CharField(max_length=30)
    card = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='checklist', null=True, blank=True)
    done = models.BooleanField(default=False, blank=True)

class Metki(models.Model):
    card = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='metki', null=True, blank=True)
    title = models.CharField(max_length=30)
    colour = models.CharField(max_length=100)
