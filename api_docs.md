# Book API Documentation

## Overview

This project is a Django REST Framework API for storing and exploring book metadata from a public Kaggle CSV dataset. It satisfies the coursework requirement for a database-backed API with CRUD functionality, JSON responses, correct HTTP status codes, rating-ranked search support, weighted recommendation support, collection statistics, and live documentation.

## Base URLs

- Home page: `http://localhost:8000/`
- Browsable API: `http://localhost:8000/api/books/`
- Swagger UI: `http://localhost:8000/api/docs/swagger/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## Data Model

Each `Book` record contains:

```json
{
  "id": 1,
  "bookid": 1,
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "genre": "Technology",
  "published_year": 2008,
  "description": "A handbook of agile software craftsmanship.",
  "pages": 464,
  "publisher": "Prentice Hall",
  "language": "en",
  "average_rating": 4.4,
  "ratings_count": 1200,
  "thumbnail": "https://example.com/clean-code.jpg"
}
```

## Public dataset integration

The project imports book metadata from the public CSV dataset stored at `archive/books.csv`. The dataset used in the current project is **Goodreads-books** by **Soumik** on Kaggle:

`https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks`

Reference:

`Soumik. 2020. Goodreads-books. [Online]. [Accessed 20 April 2026]. Available from: https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks`

The dataset includes title, authors, average rating, ISBN values, language code, page count, ratings count, text review count, publication date, and publisher. The imported dataset does not include genre, description, or thumbnail values, so imported rows use `Uncategorised` as the default genre and leave description and thumbnail blank unless edited manually.

Import command:

```bash
python manage.py import_books_dataset --replace
```

## Endpoints

### 1. List books

- Method: `GET`
- URL: `/api/books/`
- Purpose: Return all books
- Optional query parameters:
  - `bookid`: exact sequential coursework book ID
  - `genre`: exact genre match, case-insensitive
  - `author`: partial author match
  - `published_year`: exact year match
  - `search`: searches title, author, genre, and description
  - `ordering`: `bookid`, `-bookid`, `title`, `-title`, `author`, `-author`, `published_year`, `-published_year`, `average_rating`, `-average_rating`, `ratings_count`, `-ratings_count`
  - `language`: exact language code match
  - `min_rating`: minimum average rating

Example request:

```http
GET /api/books/?language=eng&min_rating=4.5&ordering=-average_rating
```

Example response:

```json
[
  {
    "id": 1,
    "bookid": 1,
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "genre": "Technology",
    "published_year": 2008,
    "description": "A handbook of agile software craftsmanship."
  }
]
```

### 2. Create a book

- Method: `POST`
- URL: `/api/books/`
- Purpose: Create a new book record

Example request body:

```json
{
  "title": "The Hobbit",
  "author": "J.R.R. Tolkien",
  "genre": "Fantasy",
  "published_year": 1937,
  "description": "A fantasy adventure novel."
}
```

Success response:

- Status: `201 Created`

Validation error example:

```json
{
  "published_year": [
    "Published year must be between 0 and 2026."
  ]
}
```

### 3. Retrieve one book

- Method: `GET`
- URL: `/api/books/{id}/`
- Purpose: Retrieve one book by the database primary key
- Success status: `200 OK`
- Not found status: `404 Not Found`

### 4. Retrieve one book by bookid

- Method: `GET`
- URL: `/api/books/by-bookid/{bookid}/`
- Purpose: Retrieve one book by the sequential coursework book ID
- Success status: `200 OK`
- Not found status: `404 Not Found`

Example request:

```http
GET /api/books/by-bookid/1/
```

### 5. Update a book

- Method: `PUT`
- URL: `/api/books/{id}/`
- Success status: `200 OK`

### 6. Delete a book

- Method: `DELETE`
- URL: `/api/books/{id}/`
- Success status: `204 No Content`

### 7. Filter books by language and rating

- Method: `GET`
- URL: `/api/books/?language=eng&min_rating=4.5`
- Purpose: Return books from the imported dataset matching a language code and minimum average rating

### 8. Book statistics

- Method: `GET`
- URL: `/api/books/stats/`
- Purpose: Return aggregate insights for the current collection

Example response:

```json
{
  "total_books": 3,
  "average_published_year": 1970.0,
  "earliest_published_year": 1937,
  "latest_published_year": 2008,
  "genres": {
    "Fantasy": 1,
    "Science Fiction": 1,
    "Technology": 1
  }
}
```

### 9. Search books

- Method: `GET`
- URL: `/api/books/search/`
- Purpose: Return rating-ranked search results from the public dataset, prioritising higher average ratings within the supplied filters and using ratings count as a secondary ranking signal
- Optional query parameters:
  - `title`
  - `author`
  - `publisher`
  - `language`
  - `min_rating`
  - `limit`

Example request:

```http
GET /api/books/search/?title=Harry%20Potter&author=J.K.%20Rowling&limit=5
```

### 10. Recommend similar books

- Method: `GET`
- URL: `/api/books/recommendations/similar/`
- Purpose: Return weighted similarity-based recommendations using a seed book selected by `bookid`
- Required query parameters:
  - `bookid`
- Optional query parameters:
  - `limit`

Recommendation weighting:

- `title` similarity: 40%
- `author` similarity: 15%
- `publisher` similarity: 10%
- `language` similarity: 15%
- `rating` quality: 15%
- `published year` closeness: 5%

The recommendation algorithm also applies diversity penalties to reduce repeated authors and near-duplicate titles in the final result list.

Example requests:

```http
GET /api/books/recommendations/similar/?bookid=1&limit=5
```

## Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Validation error or malformed input
- `401 Unauthorized`: Login required for create, update, or delete actions
- `404 Not Found`: Requested book does not exist

## Validation Rules

- `title`, `author`, and `genre` cannot be blank
- `bookid` is generated automatically and is read-only in API create/update requests
- `published_year` must be between `0` and the current year
- `description` may be blank
- `average_rating`, when present, must be between `0` and `5`
- `ratings_count` cannot be negative

## Authentication

- Read-only requests such as `GET /api/books/`, `GET /api/books/{id}/`, `GET /api/books/by-bookid/{bookid}/`, and `GET /api/books/stats/` are public.
- `GET /api/books/search/` and `GET /api/books/recommendations/similar/` are also public.
- Write operations such as `POST`, `PUT`, and `DELETE` require authentication.
- Swagger UI uses Basic Authentication, so you only need a username and password.
- For the current local setup, you can log in with the admin account created for the project.

## Demonstration Routes

- `/` provides a presentation-friendly landing page
- `/api/books/` provides the DRF browsable API
- `/api/docs/swagger/` provides interactive Swagger UI
- `/admin/` provides Django admin management
