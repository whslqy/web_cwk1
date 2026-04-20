from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('bookid', 'title', 'author', 'genre', 'published_year')
    list_filter = ('genre', 'published_year')
    search_fields = ('=bookid', 'title', 'author', 'genre')
    ordering = ('bookid',)
