
from rest_framework import serializers
from .models import Publisher, Article, Newsletter


class PublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = [
            'id',
            'name',
            'description',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'image',
            'author',
            'publisher',
            'created_at',
            'approved'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'approved'
        ]


class NewsletterSerializer(serializers.ModelSerializer):

    articles = ArticleSerializer(
        many=True,
        read_only=True
    )

    publisher = PublisherSerializer(
        read_only=True
    )

    class Meta:
        model = Newsletter
        fields = [
            'id',
            'title',
            'description',
            'author',
            'publisher',
            'articles',
            'created_at',
            'approved'
        ]
        read_only_fields = [
            'id',
            'author',
            'publisher',
            'created_at',
            'approved'
        ]
