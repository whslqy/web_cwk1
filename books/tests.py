import base64

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book


class BookAPITests(APITestCase):
    def _authenticate_as_admin(self):
        token = base64.b64encode(
            f'{self.admin_username}:{self.admin_password}'.encode('utf-8')
        ).decode('ascii')
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {token}')

    def setUp(self):
        self.admin_username = 'admin'
        self.admin_password = 'Admin12345!'
        get_user_model().objects.create_superuser(
            username=self.admin_username,
            email='admin@example.com',
            password=self.admin_password,
        )
        self.book_one = Book.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2008,
            description='A handbook of agile software craftsmanship.',
            pages=464,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.4,
            ratings_count=1200,
            thumbnail='https://example.com/clean-code.jpg',
        )
        self.book_two = Book.objects.create(
            title='Dune',
            author='Frank Herbert',
            genre='Science Fiction',
            published_year=1965,
            description='A landmark science fiction novel.',
            pages=688,
            publisher='Chilton Books',
            language='en',
            average_rating=4.6,
            ratings_count=2500,
            thumbnail='https://example.com/dune.jpg',
        )

    def test_list_books(self):
        response = self.client.get('/api/books/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_book(self):
        payload = {
            'title': 'The Hobbit',
            'author': 'J.R.R. Tolkien',
            'genre': 'Fantasy',
            'published_year': 1937,
            'description': 'A fantasy adventure novel.',
            'pages': 310,
            'publisher': 'George Allen & Unwin',
            'language': 'en',
            'average_rating': 4.7,
            'ratings_count': 3000,
            'thumbnail': 'https://example.com/hobbit.jpg',
        }

        self._authenticate_as_admin()
        response = self.client.post('/api/books/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)
        self.client.credentials()

    def test_update_book(self):
        self._authenticate_as_admin()
        response = self.client.put(
            f'/api/books/{self.book_one.id}/',
            {
                'title': self.book_one.title,
                'author': self.book_one.author,
                'genre': 'Software Engineering',
                'published_year': self.book_one.published_year,
                'description': self.book_one.description,
                'pages': self.book_one.pages,
                'publisher': self.book_one.publisher,
                'language': self.book_one.language,
                'average_rating': self.book_one.average_rating,
                'ratings_count': self.book_one.ratings_count,
                'thumbnail': self.book_one.thumbnail,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book_one.refresh_from_db()
        self.assertEqual(self.book_one.genre, 'Software Engineering')
        self.client.credentials()

    def test_delete_book(self):
        self._authenticate_as_admin()
        response = self.client.delete(f'/api/books/{self.book_two.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=self.book_two.id).exists())
        self.client.credentials()

    def test_filter_and_search_books(self):
        response = self.client.get('/api/books/', {'search': 'clean', 'genre': 'Technology'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Clean Code')

    def test_filter_by_genre(self):
        response = self.client.get('/api/books/', {'genre': 'Science Fiction'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Dune')

    def test_filter_by_min_rating(self):
        response = self.client.get('/api/books/', {'min_rating': 4.5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Dune')

    def test_filter_by_bookid(self):
        response = self.client.get('/api/books/', {'bookid': self.book_one.bookid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Clean Code')

    def test_retrieve_by_bookid(self):
        response = self.client.get(f'/api/books/by-bookid/{self.book_two.bookid}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Dune')
        self.assertEqual(response.data['bookid'], self.book_two.bookid)

    def test_stats_endpoint(self):
        response = self.client.get('/api/books/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_books'], 2)
        self.assertEqual(response.data['earliest_published_year'], 1965)
        self.assertEqual(response.data['latest_published_year'], 2008)
        self.assertEqual(response.data['genres']['Technology'], 1)

    def test_search_endpoint(self):
        response = self.client.get('/api/books/search/', {'author': 'Frank Herbert'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Dune')
        self.assertIn('match_summary', response.data[0])

    def test_search_supports_title_filter(self):
        response = self.client.get('/api/books/search/', {'title': 'clean'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Clean Code')

    def test_search_prioritises_average_rating_before_rating_count(self):
        Book.objects.create(
            title='Highly Rated Niche Book',
            author='Specialist Author',
            genre='Technology',
            published_year=2022,
            average_rating=4.9,
            ratings_count=10,
        )
        Book.objects.create(
            title='Popular But Lower Rated Book',
            author='Specialist Author',
            genre='Technology',
            published_year=2021,
            average_rating=4.2,
            ratings_count=10000,
        )

        response = self.client.get('/api/books/search/', {'author': 'Specialist Author'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], 'Highly Rated Niche Book')

    def test_similar_recommendations_by_bookid(self):
        Book.objects.create(
            title='Clean Architecture',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2017,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.5,
            ratings_count=2000,
        )
        Book.objects.create(
            title='The Clean Coder',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2011,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.4,
            ratings_count=1500,
        )

        response = self.client.get('/api/books/recommendations/similar/', {'bookid': self.book_one.bookid, 'limit': 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn(response.data[0]['title'], {'Clean Architecture', 'The Clean Coder'})
        self.assertIn('similarity_score', response.data[0])
        self.assertIn('reason', response.data[0])

    def test_similar_recommendations_apply_author_penalty_for_repeated_results(self):
        Book.objects.create(
            title='Clean Architecture',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2017,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.5,
            ratings_count=2000,
        )
        Book.objects.create(
            title='The Clean Coder',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2011,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.4,
            ratings_count=1500,
        )
        Book.objects.create(
            title='Clean Craftsmanship',
            author='Robert C. Martin',
            genre='Technology',
            published_year=2020,
            publisher='Prentice Hall',
            language='en',
            average_rating=4.3,
            ratings_count=1000,
        )
        Book.objects.create(
            title='Code Complete',
            author='Steve McConnell',
            genre='Technology',
            published_year=2004,
            publisher='Microsoft Press',
            language='en',
            average_rating=4.7,
            ratings_count=5000,
        )

        response = self.client.get('/api/books/recommendations/similar/', {'bookid': self.book_one.bookid, 'limit': 3})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data]
        self.assertIn('Code Complete', titles)
        self.assertNotIn('Clean Craftsmanship', titles)
        robert_martin_count = sum(item['author'] == 'Robert C. Martin' for item in response.data)
        self.assertLessEqual(robert_martin_count, 2)

    def test_swagger_ui_is_available(self):
        response = self.client.get(reverse('swagger-ui'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_read_is_allowed(self):
        response = self.client.get('/api/books/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_write_is_blocked(self):
        payload = {
            'title': 'Unauthorized Book',
            'author': 'Anon',
            'genre': 'Test',
            'published_year': 2020,
            'description': 'Should be rejected.',
            'ratings_count': 0,
        }

        response = self.client.post('/api/books/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reject_invalid_future_year(self):
        payload = {
            'title': 'Future Book',
            'author': 'Test Author',
            'genre': 'Speculative',
            'published_year': 9999,
            'description': 'Invalid future year.',
            'ratings_count': 0,
        }

        self._authenticate_as_admin()
        response = self.client.post('/api/books/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('published_year', response.data)
        self.client.credentials()
