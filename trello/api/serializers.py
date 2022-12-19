from rest_framework import serializers
import datetime
from trello.models import *


class CustomUserSerializer(serializers.Serializer):
    email = serializers.CharField(read_only=True)
    desk = serializers.CharField(read_only=True)


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
    author = serializers.CharField(read_only=True, default=serializers.CurrentUserDefault())
    body = serializers.CharField(max_length=500)
    created_on = serializers.DateTimeField(read_only=True)
    entry = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())

    class Meta:
        model = Comment
        fields = ['author', 'body', 'created_on', 'entry']

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
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
    docfile = serializers.FileField()

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
