from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Book
from .serializers import BookSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @action(detail=False, methods=['get'], url_path='recommend/(?P<genre>[^/.]+)')
    def recommend_by_genre(self, request, genre=None):
        books = Book.objects.filter(genre__iexact=genre)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)