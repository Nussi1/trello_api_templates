from rest_framework import serializers
import datetime
from trello.models import *
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from . import google
from .register import register_social_user
import os
from rest_framework.exceptions import AuthenticationFailed


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=68, min_length=6, write_only=True)

    default_error_messages = {
        'username': 'The username should only contain alphanumeric characters'}

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def validate(self, attrs):
        email = attrs.get('email', '')
        username = attrs.get('username', '')

        if not username.isalnum():
            raise serializers.ValidationError(
                self.default_error_messages)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=68, min_length=6, write_only=True)
    username = serializers.CharField(
        max_length=255, min_length=3, read_only=True)

    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])

        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }

    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'tokens']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        filtered_user_by_email = User.objects.filter(email=email)
        user = auth.authenticate(email=email, password=password)

        if filtered_user_by_email.exists() and filtered_user_by_email[0].auth_provider != 'email':
            raise AuthenticationFailed(
                detail='Please continue your login using ' + filtered_user_by_email[0].auth_provider)

        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens
        }

        return super().validate(attrs)


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):

        try:
            RefreshToken(self.token).blacklist()

        except TokenError:
            self.fail('bad_token')


class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = google.Google.validate(auth_token)
        try:
            user_data['sub']
        except:
            raise serializers.ValidationError(
                'The token is invalid or expired. Please login again.'
            )

        if user_data['aud'] != os.environ.get('GOOGLE_CLIENT_ID'):

            raise AuthenticationFailed('oops, who are you?')

        user_id = user_data['sub']
        email = user_data['email']
        name = user_data['name']
        provider = 'google'

        return register_social_user(
            provider=provider, user_id=user_id, email=email, name=name)


class SearchSerializer(serializers.Serializer):
    author = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)

    class Meta:
        model = MainDeskFavorites
        fields = ['author', 'label']

    def create(self, validated_data):
        label_pk = validated_data.pop('label')
        obj = CardSearch(**validated_data, label_id=label_pk, author=self.context['request'].user)
        obj.save()
        return obj


class FavouriteSerializer(serializers.Serializer):
    author = serializers.CharField(read_only=True)
    desk = serializers.CharField()

    class Meta:
        model = MainDeskFavorites
        fields = ['author', 'desk']

    def create(self, validated_data):
        desk_pk = validated_data.pop('desk')
        obj = MainDeskFavorites(**validated_data, desk_id=desk_pk, author=self.context['request'].user)
        obj.save()
        return obj


class CommentSerializer(serializers.Serializer):
    author = serializers.CharField(default=serializers.CurrentUserDefault())
    body = serializers.CharField(max_length=500)
    created_on = serializers.DateTimeField(read_only=True)
    entry = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())

    class Meta:
        model = Comment
        fields = ['author', 'body', 'created_on', 'entry']

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.author = validated_data.get('author', instance.author)
        instance.body = validated_data.get('body', instance.body)
        instance.entry = validated_data.get('entry', instance.entry)
        instance.save()
        return instance


class CardSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    column = serializers.CharField(read_only=True)
    author = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=30)
    content = serializers.CharField(max_length=300)
    date_created = serializers.DateTimeField(read_only=True)
    deadline = serializers.DateTimeField()
    choice = serializers.ChoiceField(choices=(
        ('red', 'red'),
        ('blue', 'blue'),
        ('green', 'green'),
        ('yellow', 'yellow')
    ))
    docfile = serializers.FileField(required=False)

    def create(self, validated_data):
        # print(validated_data, self.context)
        return Card.objects.create(**validated_data, column_id=self.context['column_pk'], author=self.context['request'].user)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.docfile = validated_data.get('docfile', instance.docfile)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.comments.exists():
            representation['comments'] = CommentSerializer(instance.comments.all(), many=True).data
        return representation


class ColumnSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    desk = serializers.PrimaryKeyRelatedField(queryset=MainDesk.objects.all())
    title = serializers.CharField(max_length=30)
    entries = CardSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return Column.objects.create(**validated_data, desk_id=self.context['desk_pk'])

    def update(self, instance, validated_data):
        instance.desk = validated_data.get('desk', instance.desk)
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        return instance


class MainDeskSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    author = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=30)
    created_date = serializers.DateTimeField(read_only=True)
    update = serializers.DateTimeField(initial=datetime.date.today)
    image = serializers.ImageField()
    columns = ColumnSerializer(many=True, read_only=True)
    entries = CardSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return MainDesk.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class CheckListSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=30)
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    done = serializers.BooleanField()

    class Meta:
        model = CheckList
        fields = '__all__'

    def create(self, validated_data):
        CheckList(**validated_data).save()
        return CheckList(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.done = validated_data.get('done', instance.done)
        instance.save()
        return instance

class MetkiSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=30)
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    colour = serializers.CharField(max_length=255)

    class Meta:
        model = Metki
        fields = '__all__'

    def create(self, validated_data):
        Metki(**validated_data).save()
        return Metki(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.colour = validated_data.get('colour', instance.colour)
        instance.save()
        return instance
