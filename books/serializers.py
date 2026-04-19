from rest_framework import serializers
from .models import Book
from django.utils import timezone


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Title cannot be blank.')
        return value

    def validate_author(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Author cannot be blank.')
        return value

    def validate_genre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Genre cannot be blank.')
        return value

    def validate_published_year(self, value):
        current_year = timezone.now().year
        if value < 0 or value > current_year:
            raise serializers.ValidationError(
                f'Published year must be between 0 and {current_year}.'
            )
        return value


class BookStatsSerializer(serializers.Serializer):
    total_books = serializers.IntegerField()
    average_published_year = serializers.FloatField(allow_null=True)
    earliest_published_year = serializers.IntegerField(allow_null=True)
    latest_published_year = serializers.IntegerField(allow_null=True)
    genres = serializers.DictField(child=serializers.IntegerField())
