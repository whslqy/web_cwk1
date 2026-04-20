# Book API Documentation

## Overview

This project is a Django REST Framework API for storing and exploring book metadata from a public CSV dataset. It satisfies the coursework requirement for a database-backed API with CRUD functionality, JSON responses, correct HTTP status codes, recommendation support, collection statistics, and live documentation.

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

The project imports book metadata from the public CSV dataset stored at `archive/Books.csv`. The dataset includes title, author, pages, genre, description, publication date, publisher, language, average rating, ratings count, and thumbnail URL values.

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
  - `genre`: exact genre match, case-insensitive
  - `author`: partial author match
  - `published_year`: exact year match
  - `search`: searches title, author, genre, and description
  - `ordering`: `title`, `-title`, `author`, `-author`, `published_year`, `-published_year`
  - `language`: exact language code match
  - `min_rating`: minimum average rating

Example request:

```http
GET /api/books/?genre=Technology&ordering=-published_year
```

Example response:

```json
[
  {
    "id": 1,
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
- Success status: `200 OK`
- Not found status: `404 Not Found`

### 4. Update a book

- Method: `PUT`
- URL: `/api/books/{id}/`
- Success status: `200 OK`

### 5. Delete a book

- Method: `DELETE`
- URL: `/api/books/{id}/`
- Success status: `204 No Content`

### 6. Filter books by genre

- Method: `GET`
- URL: `/api/books/?genre=Science%20Fiction`
- Purpose: Return books whose genre matches the supplied value using the main list endpoint

### 7. Book statistics

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

### 8. Recommended books

- Method: `GET`
- URL: `/api/books/recommendations/`
- Purpose: Return recommended books from the public dataset, prioritising genre and author matching and filling up to the requested limit
- Optional query parameters:
  - `genre`
  - `author`
  - `limit`

Example request:

```http
GET /api/books/recommendations/?genre=Science%20Fiction&limit=5
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
- `published_year` must be between `0` and the current year
- `description` may be blank
- `average_rating`, when present, must be between `0` and `5`
- `ratings_count` cannot be negative

## Authentication

- Read-only requests such as `GET /api/books/`, `GET /api/books/{id}/`, and `GET /api/books/stats/` are public.
- `GET /api/books/recommendations/` is also public.
- Write operations such as `POST`, `PUT`, and `DELETE` require authentication.
- Swagger UI uses Basic Authentication, so you only need a username and password.
- For the current local setup, you can log in with the admin account created for the project.

## Demonstration Routes

- `/` provides a presentation-friendly landing page
- `/api/books/` provides the DRF browsable API
- `/api/docs/swagger/` provides interactive Swagger UI
- `/admin/` provides Django admin management
