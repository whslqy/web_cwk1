from django.db import models
from django.db.models import Max

class Book(models.Model):
    bookid = models.PositiveIntegerField(unique=True, null=True, blank=True, db_index=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    published_year = models.IntegerField()
    description = models.TextField(blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=20, blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    ratings_count = models.PositiveIntegerField(default=0)
    thumbnail = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        if self.bookid is None:
            max_bookid = Book.objects.aggregate(max_bookid=Max('bookid'))['max_bookid'] or 0
            self.bookid = max_bookid + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
