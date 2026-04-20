from django.db.models import Avg, Count, Max, Min, Q
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Book
from .serializers import BookSerializer, BookStatsSerializer, RecommendationSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    ordering = ['title']
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Book.objects.all().order_by('title', 'id')
        params = self.request.query_params

        genre = params.get('genre')
        author = params.get('author')
        year = params.get('published_year')
        search = params.get('search')
        ordering = params.get('ordering')
        min_rating = params.get('min_rating')
        language = params.get('language')

        if genre:
            queryset = queryset.filter(genre__iexact=genre.strip())
        if author:
            queryset = queryset.filter(author__icontains=author.strip())
        if year:
            queryset = queryset.filter(published_year=year)
        if search:
            search = search.strip()
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(author__icontains=search)
                | Q(genre__icontains=search)
                | Q(description__icontains=search)
            )
        if min_rating:
            try:
                queryset = queryset.filter(average_rating__gte=float(min_rating))
            except ValueError:
                queryset = queryset.none()
        if language:
            queryset = queryset.filter(language__iexact=language.strip())
        if ordering in {'title', '-title', 'published_year', '-published_year', 'author', '-author'}:
            queryset = queryset.order_by(ordering, 'id')

        return queryset

    @extend_schema(
        summary='List books',
        description='Returns all books and supports filtering, search, and ordering through query parameters.',
        parameters=[
            OpenApiParameter(name='genre', description='Filter by exact genre, case-insensitive.', required=False, type=str),
            OpenApiParameter(name='author', description='Filter by author name containing the given text.', required=False, type=str),
            OpenApiParameter(name='published_year', description='Filter by exact publication year.', required=False, type=int),
            OpenApiParameter(name='search', description='Search title, author, genre, and description.', required=False, type=str),
            OpenApiParameter(name='ordering', description='Sort by title, author, or published_year. Prefix with - for descending.', required=False, type=str),
            OpenApiParameter(name='language', description='Filter by language code, for example en.', required=False, type=str),
            OpenApiParameter(name='min_rating', description='Filter by minimum average rating.', required=False, type=float),
        ],
        examples=[
            OpenApiExample(
                'Filtered list example',
                value=[
                    {
                        'id': 1,
                        'title': 'The Pragmatic Programmer',
                        'author': 'Andrew Hunt',
                        'genre': 'Technology',
                        'published_year': 1999,
                        'description': 'Classic software craftsmanship guidance.',
                    }
                ],
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create a book',
        description='Creates a new book record in the database.',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Retrieve a single book',
        description='Returns one book by ID.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update a book',
        description='Replaces an existing book record.',
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete a book',
        description='Removes a book from the database.',
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Book statistics',
        description='Returns aggregate statistics for the current book collection.',
        responses=BookStatsSerializer,
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        queryset = self.get_queryset()
        aggregates = queryset.aggregate(
            total_books=Count('id'),
            average_published_year=Avg('published_year'),
            earliest_published_year=Min('published_year'),
            latest_published_year=Max('published_year'),
        )
        genre_counts = queryset.values('genre').annotate(count=Count('id')).order_by('genre')
        data = {
            **aggregates,
            'genres': {row['genre']: row['count'] for row in genre_counts},
        }
        serializer = BookStatsSerializer(data)
        return Response(serializer.data)

    @extend_schema(
        summary='Recommend books',
        description='Returns recommended books, optionally narrowed by genre or author text.',
        parameters=[
            OpenApiParameter(name='genre', description='Optional genre for recommendations.', required=False, type=str),
            OpenApiParameter(name='author', description='Optional author text filter.', required=False, type=str),
            OpenApiParameter(name='limit', description='Maximum number of recommendations to return.', required=False, type=int),
        ],
        responses=RecommendationSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='recommendations')
    def recommendations(self, request):
        queryset = Book.objects.all()
        genre = request.query_params.get('genre')
        author = request.query_params.get('author')
        limit = request.query_params.get('limit', '10')

        normalized_genre = genre.strip() if genre else ''
        if normalized_genre:
            queryset = queryset.filter(genre__iexact=normalized_genre)
        if author:
            queryset = queryset.filter(author__icontains=author.strip())

        try:
            limit = max(1, min(int(limit), 20))
        except ValueError:
            limit = 10

        books = list(queryset.order_by('-ratings_count', '-average_rating', 'title')[:limit])

        if normalized_genre and len(books) < limit:
            books = self._expand_recommendations_with_related_genres(
                books=books,
                genre=normalized_genre,
                author=author,
                limit=limit,
            )

        data = [
            {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'published_year': book.published_year,
                'average_rating': book.average_rating,
                'ratings_count': book.ratings_count,
                'reason': self._build_recommendation_reason(book),
            }
            for book in books
        ]
        return Response(data)

    def _expand_recommendations_with_related_genres(self, books, genre, author, limit):
        existing_ids = {book.id for book in books}
        related_queryset = Book.objects.exclude(id__in=existing_ids)

        if author:
            related_queryset = related_queryset.filter(author__icontains=author.strip())

        token_filters = Q()
        for token in genre.lower().split():
            if len(token) >= 4:
                token_filters |= Q(genre__icontains=token)

        if token_filters:
            extras = list(
                related_queryset.filter(token_filters)
                .order_by('-ratings_count', '-average_rating', 'title')[: max(0, limit - len(books))]
            )
            books.extend(extras)

        return books[:limit]

    def _build_recommendation_reason(self, book):
        if book.average_rating is not None and book.ratings_count > 0:
            return (
                f'Recommended from the {book.genre} genre with {book.average_rating:.2f} average rating '
                f'from {book.ratings_count} ratings.'
            )
        return (
            f'Recommended from the {book.genre} genre based on metadata matching. '
            'This dataset entry has limited rating information.'
        )
