import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from books.models import Book


class Command(BaseCommand):
    help = 'Import books from the public CSV dataset in archive/books.csv.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            default='archive/books.csv',
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
            for row in self._iter_dataset_rows(handle):
                if limit is not None and imported >= limit:
                    break

                title = self._get_value(row, 'title')
                author = self._get_value(row, 'author', 'authors') or 'Unknown'
                genre = self._get_value(row, 'genre') or 'Uncategorised'
                description = self._get_value(row, 'description')

                if not title:
                    skipped += 1
                    continue

                published_year = self._parse_year(
                    self._get_value(row, 'published_date', 'publication_date')
                )
                if published_year is None:
                    skipped += 1
                    continue

                defaults = {
                    'author': author[:255],
                    'genre': genre[:100],
                    'published_year': published_year,
                    'description': '' if description == 'No description available' else description,
                    'pages': self._parse_int(self._get_value(row, 'pages', 'num_pages')),
                    'publisher': self._get_value(row, 'publisher')[:255],
                    'language': self._get_value(row, 'language', 'language_code')[:20],
                    'average_rating': self._parse_rating(self._get_value(row, 'average_rating')),
                    'ratings_count': self._parse_int(self._get_value(row, 'ratings_count')) or 0,
                    'thumbnail': self._get_value(row, 'thumbnail'),
                }
                Book.objects.update_or_create(
                    title=title[:200],
                    author=defaults['author'],
                    defaults=defaults,
                )
                imported += 1

        self._renumber_bookids()
        self.stdout.write(self.style.SUCCESS(f'Imported {imported} books; skipped {skipped} rows.'))

    def _iter_dataset_rows(self, handle):
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return

        normalized_header = [column.strip().lower() for column in header]
        is_goodreads_format = {
            'bookid',
            'title',
            'authors',
            'average_rating',
            'publication_date',
        }.issubset(set(normalized_header))

        if is_goodreads_format:
            for raw_row in reader:
                row = self._normalize_goodreads_row(raw_row)
                if row is not None:
                    yield row
            return

        for raw_row in reader:
            yield {
                key: raw_row[index] if index < len(raw_row) else ''
                for index, key in enumerate(normalized_header)
            }

    def _normalize_goodreads_row(self, raw_row):
        if len(raw_row) < 12:
            return None

        # The Goodreads CSV has a few unquoted commas in author names, so parse
        # fixed fields from the right and merge the middle section as authors.
        return {
            'bookid': raw_row[0].strip(),
            'title': raw_row[1].strip(),
            'authors': ','.join(value.strip() for value in raw_row[2:-9] if value.strip()),
            'average_rating': raw_row[-9].strip(),
            'isbn': raw_row[-8].strip(),
            'isbn13': raw_row[-7].strip(),
            'language_code': raw_row[-6].strip(),
            'num_pages': raw_row[-5].strip(),
            'ratings_count': raw_row[-4].strip(),
            'text_reviews_count': raw_row[-3].strip(),
            'publication_date': raw_row[-2].strip(),
            'publisher': raw_row[-1].strip(),
        }

    def _get_value(self, row, *names):
        for name in names:
            value = row.get(name.strip().lower())
            if value is not None:
                return value.strip()
        return ''

    def _renumber_bookids(self):
        Book.objects.update(bookid=None)
        for index, book in enumerate(Book.objects.order_by('id'), start=1):
            Book.objects.filter(pk=book.pk).update(bookid=index)

    def _parse_year(self, value):
        value = (value or '').strip()
        if not value:
            return None
        for date_format in ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%Y/%m/%d'):
            try:
                return datetime.strptime(value, date_format).year
            except ValueError:
                pass
        parts = value.replace('-', '/').split('/')
        if parts and parts[-1].strip().isdigit() and len(parts[-1].strip()) == 4:
            return int(parts[-1].strip())
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
