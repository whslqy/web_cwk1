# Book API Coursework Project

This repository contains a Django REST Framework project for managing and exploring books. It is designed to satisfy the coursework requirement for a database-backed API with full CRUD functionality, a public dataset import workflow, interactive documentation, JSON responses, error handling, and a browsable demonstration interface.

## Features

- Full CRUD operations for a `Book` model
- SQLite database integration
- Search, filtering, and ordering on the collection endpoint
- Genre filtering through the main collection endpoint
- Public dataset import from `archive/Books.csv`
- Recommendation endpoint for metadata-based book suggestions
- Aggregate statistics endpoint
- Swagger UI and ReDoc documentation generated from the live API schema
- DRF browsable API for local demonstration
- Django admin with search and filtering
- Automated API tests

## Project structure

- `bookapi/` Django project configuration
- `books/` API app with model, serializer, viewset, admin, and tests
- `templates/home.html` landing page with links for demonstration
- `api_docs.md` manual API documentation
- `archive/Books.csv` public book metadata dataset
- `XJCO3011_Coursework1_Brief__2025_2026.pdf` coursework brief

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Import the public dataset:

```bash
python manage.py import_books_dataset --replace
```

5. Start the development server:

```bash
python manage.py runserver
```

6. Open the project at `http://localhost:8000/`

## Main URLs

- Home page: `http://localhost:8000/`
- Browsable API: `http://localhost:8000/api/books/`
- Swagger UI: `http://localhost:8000/api/docs/swagger/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Admin: `http://localhost:8000/admin/`

## API documentation

- Manual documentation: `api_docs.md`
- Submission-ready PDF: `Book_API_Documentation.pdf`
- Interactive documentation: Swagger UI at `/api/docs/swagger/`

## Authentication behaviour

- Public read access: `GET` requests can be used without logging in
- Protected write access: `POST`, `PUT`, and `DELETE` require authentication
- Swagger authentication method: Basic Auth with username and password

## Example API usage

Create a book:

```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Dune\",\"author\":\"Frank Herbert\",\"genre\":\"Science Fiction\",\"published_year\":1965,\"description\":\"Classic sci-fi novel.\"}"
```

List books:

```bash
curl http://localhost:8000/api/books/
```

Get recommendations by genre:

```bash
curl "http://localhost:8000/api/books/?genre=Science%20Fiction"
```

View collection statistics:

```bash
curl http://localhost:8000/api/books/stats/
```

Get recommendations:

```bash
curl "http://localhost:8000/api/books/recommendations/?genre=Science%20Fiction&limit=5"
```

## Testing

Run the automated test suite with:

```bash
python manage.py test
```
