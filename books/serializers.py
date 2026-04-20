from rest_framework import serializers
from .models import Book
from django.utils import timezone


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('bookid',)

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

    def validate_average_rating(self, value):
        if value is not None and (value < 0 or value > 5):
            raise serializers.ValidationError('Average rating must be between 0 and 5.')
        return value

    def validate_ratings_count(self, value):
        if value < 0:
            raise serializers.ValidationError('Ratings count cannot be negative.')
        return value


class BookStatsSerializer(serializers.Serializer):
    total_books = serializers.IntegerField()
    average_published_year = serializers.FloatField(allow_null=True)
    earliest_published_year = serializers.IntegerField(allow_null=True)
    latest_published_year = serializers.IntegerField(allow_null=True)
    genres = serializers.DictField(child=serializers.IntegerField())


class SearchQuerySerializer(serializers.Serializer):
    title = serializers.CharField(required=False, help_text='Optional title text filter.')
    author = serializers.CharField(required=False, help_text='Optional author text filter.')
    publisher = serializers.CharField(required=False, help_text='Optional publisher text filter.')
    language = serializers.CharField(required=False, help_text='Optional language code filter, for example eng or en-US.')
    min_rating = serializers.FloatField(required=False, help_text='Optional minimum average rating.')
    limit = serializers.IntegerField(required=False, help_text='Maximum number of search results to return.')


class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    bookid = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    author = serializers.CharField()
    genre = serializers.CharField()
    published_year = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    ratings_count = serializers.IntegerField()
    match_summary = serializers.CharField()


class RecommendationResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    bookid = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    author = serializers.CharField()
    genre = serializers.CharField()
    publisher = serializers.CharField(allow_blank=True)
    language = serializers.CharField(allow_blank=True)
    published_year = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    ratings_count = serializers.IntegerField()
    similarity_score = serializers.FloatField()
    reason = serializers.CharField()
