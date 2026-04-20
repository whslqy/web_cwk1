import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from books.models import Book


class Command(BaseCommand):
    help = 'Import books from the public CSV dataset in archive/Books.csv.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            default='archive/Books.csv',
            help='Path to the CSV dataset file.',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing books before importing.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Optional number of rows to import.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        if options['replace']:
            deleted, _ = Book.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing records.'))

        imported = 0
        skipped = 0
        limit = options['limit']

        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if limit is not None and imported >= limit:
                    break

                title = (row.get('title') or '').strip()
                author = (row.get('author') or '').strip() or 'Unknown'
                genre = (row.get('genre') or '').strip() or 'Unknown'
                description = (row.get('description') or '').strip()

                if not title:
                    skipped += 1
                    continue

                published_year = self._parse_year(row.get('published_date'))
                if published_year is None:
                    skipped += 1
                    continue

                defaults = {
                    'author': author[:255],
                    'genre': genre[:100],
                    'published_year': published_year,
                    'description': '' if description == 'No description available' else description,
                    'pages': self._parse_int(row.get('pages')),
                    'publisher': (row.get('publisher') or '').strip()[:255],
                    'language': (row.get('language') or '').strip()[:20],
                    'average_rating': self._parse_rating(row.get('average_rating')),
                    'ratings_count': self._parse_int(row.get('ratings_count')) or 0,
                    'thumbnail': (row.get('thumbnail') or '').strip(),
                }
                Book.objects.update_or_create(
                    title=title[:200],
                    author=defaults['author'],
                    defaults=defaults,
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {imported} books; skipped {skipped} rows.'))

    def _parse_year(self, value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            return int(value[:4])
        except ValueError:
            return None

    def _parse_int(self, value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            return int(float(value))
        except ValueError:
            return None

    def _parse_rating(self, value):
        value = (value or '').strip()
        if not value or value.lower() == 'no rating':
            return None
        try:
            return float(value)
        except ValueError:
            return None
