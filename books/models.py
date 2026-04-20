from django.db import models

class Book(models.Model):
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

    def __str__(self):
        return self.title
