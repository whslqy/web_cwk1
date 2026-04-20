import math
import re
from difflib import SequenceMatcher

from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Book
from .serializers import (
    BookSerializer,
    BookStatsSerializer,
    RecommendationResultSerializer,
    SearchQuerySerializer,
    SearchResultSerializer,
)


TITLE_STOPWORDS = {
    'the', 'a', 'an', 'of', 'and', 'to', 'in', 'for', 'on', 'with', 'by',
    'from', 'at', 'is', 'it', 'its', 'into', 'or', 'as', 'be', 'this', 'that',
}


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
        bookid = params.get('bookid')

        if bookid:
            try:
                queryset = queryset.filter(bookid=int(bookid))
            except ValueError:
                queryset = queryset.none()
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
        allowed_ordering = {
            'title',
            '-title',
            'published_year',
            '-published_year',
            'author',
            '-author',
            'average_rating',
            '-average_rating',
            'ratings_count',
            '-ratings_count',
            'bookid',
            '-bookid',
        }
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering, 'id')

        return queryset

    @extend_schema(
        summary='List books',
        description='Returns all books and supports filtering, search, and ordering through query parameters.',
        parameters=[
            OpenApiParameter(name='genre', description='Filter by exact genre, case-insensitive.', required=False, type=str),
            OpenApiParameter(name='bookid', description='Filter by the sequential coursework book ID.', required=False, type=int),
            OpenApiParameter(name='author', description='Filter by author name containing the given text.', required=False, type=str),
            OpenApiParameter(name='published_year', description='Filter by exact publication year.', required=False, type=int),
            OpenApiParameter(name='search', description='Search title, author, genre, and description.', required=False, type=str),
            OpenApiParameter(name='ordering', description='Sort by bookid, title, author, published_year, average_rating, or ratings_count. Prefix with - for descending.', required=False, type=str),
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
        summary='Retrieve a book by bookid',
        description='Returns one book using the sequential coursework bookid instead of the database primary key.',
        parameters=[
            OpenApiParameter(
                name='bookid',
                description='Sequential coursework book ID.',
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses=BookSerializer,
    )
    @action(detail=False, methods=['get'], url_path=r'by-bookid/(?P<bookid>[0-9]+)')
    def by_bookid(self, request, bookid=None):
        book = get_object_or_404(Book, bookid=bookid)
        serializer = self.get_serializer(book)
        return Response(serializer.data)

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
        summary='Search books',
        description=(
            'Searches books by title, author, publisher, language, and rating. '
            'Results are sorted by average rating first and ratings count second.'
        ),
        parameters=[SearchQuerySerializer],
        responses=SearchResultSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        queryset = Book.objects.all()
        title = request.query_params.get('title')
        author = request.query_params.get('author')
        publisher = request.query_params.get('publisher')
        language = request.query_params.get('language')
        min_rating = request.query_params.get('min_rating')
        limit = request.query_params.get('limit', '10')

        if title:
            queryset = queryset.filter(title__icontains=title.strip())
        if author:
            queryset = queryset.filter(author__icontains=author.strip())
        if publisher:
            queryset = queryset.filter(publisher__icontains=publisher.strip())
        if language:
            queryset = queryset.filter(language__iexact=language.strip())
        if min_rating:
            try:
                queryset = queryset.filter(average_rating__gte=float(min_rating))
            except ValueError:
                queryset = queryset.none()

        try:
            limit = max(1, min(int(limit), 20))
        except ValueError:
            limit = 10

        books = list(queryset.order_by('-average_rating', '-ratings_count', 'title')[:limit])

        data = [
            {
                'id': book.id,
                'bookid': book.bookid,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'published_year': book.published_year,
                'average_rating': book.average_rating,
                'ratings_count': book.ratings_count,
                'match_summary': self._build_search_match_summary(book),
            }
            for book in books
        ]
        return Response(data)

    def _build_search_match_summary(self, book):
        if book.average_rating is not None and book.ratings_count > 0:
            return (
                f'Matched search result with {book.average_rating:.2f} average rating from '
                f'{book.ratings_count} ratings.'
            )
        return (
            'Matched search result based on metadata. This dataset entry has limited rating information.'
        )

    @extend_schema(
        summary='Recommend similar books',
        description=(
            'Finds books similar to a seed book identified by bookid. '
            'The score uses weighted title, author, publisher, language, rating, and year signals, '
            'plus diversity penalties to reduce repeated authors and near-duplicate titles.'
        ),
        parameters=[
            OpenApiParameter(name='bookid', description='Sequential coursework book ID of the seed book.', required=True, type=int),
            OpenApiParameter(name='limit', description='Maximum number of similar books to return.', required=False, type=int),
        ],
        responses=RecommendationResultSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='recommendations/similar')
    def similar_recommendations(self, request):
        seed_book = self._resolve_seed_book(request)
        limit = self._parse_limit(request.query_params.get('limit', '5'), default=5, maximum=20)

        candidate_books = list(Book.objects.exclude(id=seed_book.id))
        scored_candidates = []
        for candidate in candidate_books:
            signals = self._calculate_similarity_signals(seed_book, candidate)
            base_score = self._calculate_base_score(signals)
            scored_candidates.append(
                {
                    'book': candidate,
                    'signals': signals,
                    'base_score': base_score,
                }
            )

        selected = self._select_diverse_recommendations(scored_candidates, limit)
        data = [
            {
                'id': item['book'].id,
                'bookid': item['book'].bookid,
                'title': item['book'].title,
                'author': item['book'].author,
                'genre': item['book'].genre,
                'publisher': item['book'].publisher,
                'language': item['book'].language,
                'published_year': item['book'].published_year,
                'average_rating': item['book'].average_rating,
                'ratings_count': item['book'].ratings_count,
                'similarity_score': round(item['final_score'], 4),
                'reason': self._build_recommendation_reason(item['signals']),
            }
            for item in selected
        ]
        return Response(data)

    def _resolve_seed_book(self, request):
        bookid = request.query_params.get('bookid')

        if bookid:
            try:
                return get_object_or_404(Book, bookid=int(bookid))
            except ValueError:
                return get_object_or_404(Book, pk=-1)

        return get_object_or_404(Book, pk=-1)

    def _parse_limit(self, raw_limit, default=10, maximum=20):
        try:
            return max(1, min(int(raw_limit), maximum))
        except (TypeError, ValueError):
            return default

    def _calculate_similarity_signals(self, seed_book, candidate):
        title_score = self._calculate_title_score(seed_book.title, candidate.title)
        author_score = self._calculate_author_score(seed_book.author, candidate.author)
        publisher_score = self._calculate_publisher_score(seed_book.publisher, candidate.publisher)
        language_score = self._calculate_language_score(seed_book.language, candidate.language)
        rating_score = self._calculate_rating_score(candidate.average_rating, candidate.ratings_count)
        year_score = self._calculate_year_score(seed_book.published_year, candidate.published_year)
        return {
            'title_score': title_score,
            'author_score': author_score,
            'publisher_score': publisher_score,
            'language_score': language_score,
            'rating_score': rating_score,
            'year_score': year_score,
        }

    def _calculate_base_score(self, signals):
        return (
            0.40 * signals['title_score']
            + 0.15 * signals['author_score']
            + 0.10 * signals['publisher_score']
            + 0.15 * signals['language_score']
            + 0.15 * signals['rating_score']
            + 0.05 * signals['year_score']
        )

    def _select_diverse_recommendations(self, scored_candidates, limit):
        selected = []
        remaining = scored_candidates[:]

        while remaining and len(selected) < limit:
            best_item = None
            best_score = -1.0
            for item in remaining:
                adjusted_score = self._apply_diversity_penalty(item, selected)
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_item = {
                        **item,
                        'final_score': adjusted_score,
                    }

            if best_item is None:
                break

            selected.append(best_item)
            remaining = [item for item in remaining if item['book'].id != best_item['book'].id]

        return selected

    def _apply_diversity_penalty(self, item, selected):
        if not selected:
            return item['base_score']

        author_overlap_count = 0
        highly_similar_title_count = 0
        candidate_authors = self._split_authors(item['book'].author)
        candidate_title_tokens = self._tokenize_title(item['book'].title)

        for chosen in selected:
            chosen_authors = self._split_authors(chosen['book'].author)
            if candidate_authors and chosen_authors and candidate_authors.intersection(chosen_authors):
                author_overlap_count += 1

            chosen_title_tokens = self._tokenize_title(chosen['book'].title)
            title_similarity = self._title_token_jaccard(candidate_title_tokens, chosen_title_tokens)
            if title_similarity > 0.75:
                highly_similar_title_count += 1

        penalty_author = self._author_penalty(author_overlap_count)
        penalty_title = self._title_penalty(highly_similar_title_count)
        combined_penalty = max(0.15, penalty_author * penalty_title)
        return item['base_score'] * combined_penalty

    def _author_penalty(self, overlap_count):
        if overlap_count <= 0:
            return 1.0
        if overlap_count == 1:
            return 0.7
        if overlap_count == 2:
            return 0.4
        return 0.2

    def _title_penalty(self, similar_title_count):
        if similar_title_count <= 0:
            return 1.0
        if similar_title_count == 1:
            return 0.7
        return 0.4

    def _calculate_title_score(self, seed_title, candidate_title):
        seed_tokens = self._tokenize_title(seed_title)
        candidate_tokens = self._tokenize_title(candidate_title)
        token_score = self._title_token_jaccard(seed_tokens, candidate_tokens)
        sequence_score = self._title_sequence_ratio(seed_title, candidate_title)
        return 0.7 * token_score + 0.3 * sequence_score

    def _tokenize_title(self, title):
        normalized = re.sub(r'[^a-z0-9\s]+', ' ', (title or '').lower())
        return {
            token for token in normalized.split()
            if len(token) >= 3 and token not in TITLE_STOPWORDS
        }

    def _title_token_jaccard(self, seed_tokens, candidate_tokens):
        if not seed_tokens or not candidate_tokens:
            return 0.0
        union = seed_tokens.union(candidate_tokens)
        if not union:
            return 0.0
        return len(seed_tokens.intersection(candidate_tokens)) / len(union)

    def _title_sequence_ratio(self, seed_title, candidate_title):
        left = re.sub(r'\s+', ' ', (seed_title or '').strip().lower())
        right = re.sub(r'\s+', ' ', (candidate_title or '').strip().lower())
        if not left or not right:
            return 0.0
        return SequenceMatcher(None, left, right).ratio()

    def _split_authors(self, author_value):
        return {
            part.strip().lower()
            for part in (author_value or '').split('/')
            if part.strip()
        }

    def _calculate_author_score(self, seed_author, candidate_author):
        seed_authors = self._split_authors(seed_author)
        candidate_authors = self._split_authors(candidate_author)
        if not seed_authors or not candidate_authors:
            return 0.0
        if seed_authors == candidate_authors:
            return 1.0
        if seed_authors.intersection(candidate_authors):
            return 0.7
        return 0.0

    def _normalize_text(self, value):
        return re.sub(r'\s+', ' ', (value or '').strip().lower())

    def _calculate_publisher_score(self, seed_publisher, candidate_publisher):
        left = self._normalize_text(seed_publisher)
        right = self._normalize_text(candidate_publisher)
        if not left or not right:
            return 0.0
        if left == right:
            return 1.0
        if left in right or right in left:
            return 0.5
        return 0.0

    def _calculate_language_score(self, seed_language, candidate_language):
        left = self._normalize_text(seed_language)
        right = self._normalize_text(candidate_language)
        if not left or not right:
            return 0.0
        return 1.0 if left == right else 0.0

    def _calculate_rating_score(self, average_rating, ratings_count):
        normalized_rating = 0.0 if average_rating is None else max(0.0, min(average_rating / 5.0, 1.0))
        confidence = min(math.log10((ratings_count or 0) + 1) / 6, 1.0)
        return 0.7 * normalized_rating + 0.3 * confidence

    def _calculate_year_score(self, seed_year, candidate_year):
        if seed_year is None or candidate_year is None:
            return 0.0
        return max(0.0, 1 - abs(seed_year - candidate_year) / 20)

    def _build_recommendation_reason(self, signals):
        reason_parts = []
        if signals['title_score'] >= 0.35:
            reason_parts.append('strong title similarity')
        if signals['author_score'] >= 0.7:
            reason_parts.append('shared author information')
        if signals['publisher_score'] >= 0.5:
            reason_parts.append('matching publisher')
        if signals['language_score'] >= 1.0:
            reason_parts.append('same language')
        if signals['rating_score'] >= 0.6:
            reason_parts.append('strong rating quality')
        if signals['year_score'] >= 0.7:
            reason_parts.append('similar publication period')

        if not reason_parts:
            return 'Recommended using weighted similarity across title, author, publisher, language, rating, and year.'

        return 'Recommended because of ' + ', '.join(reason_parts) + '.'
