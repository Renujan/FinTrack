# Personal Finance Tracker SaaS - Backend

A scalable, secure Personal Finance Tracker SaaS backend application built with **Django REST Framework (DRF)** and **PostgreSQL**.

---

## 🏗️ Architecture Overview

The system follows clean modular monolithic architecture designed for SaaS scalability:
- **Custom Authentication Layer**: Built on top of Django's `AbstractUser` to support flexible multi-currency financial profiles.
- **Database Architecture**: Powered by PostgreSQL for relational data integrity, transactional safety, and index-optimized queries.
- **RESTful API Infrastructure**: Built with Django REST Framework (DRF) preparing standard JSON endpoints for React frontend integration.
- **Environment Isolation**: Configured using `python-dotenv` for zero hardcoded secrets across development and production environments.

---

## 🛠️ Tech Stack

- **Backend Framework**: Django 5.x / Django REST Framework
- **Database Engine**: PostgreSQL 18
- **Language**: Python 3.10+
- **Environment Management**: `python-dotenv`
- **Testing Framework**: `pytest`, `pytest-django`
- **Version Control**: Git

---

## 🗺️ Multi-Day Development Roadmap

- [x] **Day 1**: Backend Foundation (Django structure, PostgreSQL integration, custom User model, pytest configuration, environment setup).
- [x] **Day 2**: Authentication & User Management (JWT auth with SimpleJWT, registration, login, logout token blacklist, user profile API, automated tests).
- [x] **Day 3**: Transaction & Category Foundation (Categories, Income & Expense Transactions, ownership permissions, filtering, pagination, tests).
- [x] **Day 4**: Category Management & Advanced Transaction Filtering (Category CRUD, category protection, search, type/category/date/amount filters, sorting, pagination, validation, security, tests, docs).
- [ ] **Day 5**: Frontend Integration (React + Tailwind CSS SaaS dashboard).

---

## 📋 Day 1 Project Setup & Local Development

Follow these step-by-step instructions to set up the backend locally:

### 1. Prerequisites
- Python 3.10+ installed
- PostgreSQL 18 installed and running on `localhost:5432`
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/Renujan/FinTrack.git
cd FinTrack
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. PostgreSQL Database Creation
Ensure PostgreSQL is running locally and create the database:
```sql
CREATE DATABASE finance_tracker_db;
```

### 6. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```bash
cp .env.example .env
```

---

## 🔑 Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Unique Django cryptographic secret key |
| `DEBUG` | `True` | Debug mode toggle (`True`/`False`) |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated list of allowed hostnames |
| `DB_NAME` | `finance_tracker_db` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL database username |
| `DB_PASSWORD` | `postgres` | PostgreSQL database password |
| `DB_HOST` | `127.0.0.1` | PostgreSQL host address |
| `DB_PORT` | `5432` | PostgreSQL port number |

---

## 🔐 Authentication API Documentation

Base URL: `/api/auth/`

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | No | Register a new user account |
| `POST` | `/api/auth/login/` | No | Authenticate user and receive JWT access/refresh tokens |
| `POST` | `/api/auth/token/refresh/` | No | Refresh an expired access token using valid refresh token |
| `POST` | `/api/auth/logout/` | Yes (`Bearer`) | Blacklist refresh token for secure logout |
| `GET` | `/api/auth/profile/` | Yes (`Bearer`) | Retrieve current user's profile details |
| `PUT` / `PATCH` | `/api/auth/profile/` | Yes (`Bearer`) | Update current user's username, email, or primary currency |

---

### Request & Response Examples

#### 1. User Registration
`POST /api/auth/register/`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "currency": "USD"
}
```

**Response (`201 Created`):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "currency": "USD"
  }
}
```

#### 2. User Login
`POST /api/auth/login/`

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 💸 Category & Transaction Management API Documentation

Base URL: `/api/`

### 🏷️ Categories API

All Category endpoints require `Authorization: Bearer <access_token>` header.

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/categories/` | Yes (`Bearer`) | List all categories belonging to the authenticated user |
| `POST` | `/api/categories/` | Yes (`Bearer`) | Create a category for the authenticated user |
| `GET` | `/api/categories/<id>/` | Yes (`Bearer`) | Retrieve a specific category owned by user |
| `PUT` | `/api/categories/<id>/` | Yes (`Bearer`) | Full update of a category name |
| `PATCH` | `/api/categories/<id>/` | Yes (`Bearer`) | Partial update of a category name |
| `DELETE` | `/api/categories/<id>/` | Yes (`Bearer`) | Delete a category (protected if used in transactions) |

#### Category Examples

**Create Category (`POST /api/categories/`)**:
```json
{
  "name": "Groceries"
}
```

**Response (`201 Created`)**:
```json
{
  "id": 1,
  "name": "Groceries",
  "created_at": "2026-08-13T09:40:00Z",
  "updated_at": "2026-08-13T09:40:00Z"
}
```

---

### 💳 Transactions API

All Transaction endpoints require `Authorization: Bearer <access_token>` header.

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/transactions/` | Yes (`Bearer`) | List, search, filter, sort, and paginate transactions |
| `POST` | `/api/transactions/` | Yes (`Bearer`) | Create a new transaction (income/expense) |
| `GET` | `/api/transactions/<id>/` | Yes (`Bearer`) | Retrieve transaction detail |
| `PUT` | `/api/transactions/<id>/` | Yes (`Bearer`) | Full update of a transaction |
| `PATCH` | `/api/transactions/<id>/` | Yes (`Bearer`) | Partial update of a transaction |
| `DELETE` | `/api/transactions/<id>/` | Yes (`Bearer`) | Delete a transaction |

#### Query Parameters Reference

##### 1. Search Parameter (`search`)
Search transactions by description or category name (case-insensitive).
- Example: `/api/transactions/?search=supermarket`

##### 2. Filter Parameters
- `type`: Filter by transaction type (`INCOME`, `EXPENSE`). Example: `/api/transactions/?type=expense`
- `category`: Filter by category name or category ID. Example: `/api/transactions/?category=Groceries`
- `date`: Filter by exact date (YYYY-MM-DD). Example: `/api/transactions/?date=2026-08-12`
- `start_date` / `end_date`: Filter by date range. Example: `/api/transactions/?start_date=2026-08-01&end_date=2026-08-31`
- `min_amount` / `max_amount`: Filter by amount range. Example: `/api/transactions/?min_amount=100&max_amount=500`

Multiple filters can be combined:
- Example: `/api/transactions/?type=expense&category=Groceries&min_amount=50&start_date=2026-08-01`

##### 3. Sorting Parameter (`ordering`)
Allowed ordering fields: `date`, `transaction_date`, `amount`, `created_at` (prefix with `-` for descending).
- Ascending date: `/api/transactions/?ordering=date` or `/api/transactions/?ordering=transaction_date`
- Descending date: `/api/transactions/?ordering=-date` or `/api/transactions/?ordering=-transaction_date`
- Ascending amount: `/api/transactions/?ordering=amount`
- Descending amount: `/api/transactions/?ordering=-amount`
- Default ordering: `['-date', '-created_at']`

##### 4. Pagination Parameters (`page`, `page_size`)
- Default page size: `10`
- Maximum page size: `100`
- Example: `/api/transactions/?page=1&page_size=20`

#### Paginated Response Example (`200 OK`)
```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 12,
      "category": 1,
      "category_name": "Groceries",
      "transaction_type": "EXPENSE",
      "amount": "125.50",
      "description": "Weekly supermarket shopping",
      "date": "2026-08-12",
      "created_at": "2026-08-12T14:30:00Z",
      "updated_at": "2026-08-12T14:30:00Z"
    }
  ]
}
```

---

## 🧪 Testing Guide

We use `pytest` and `pytest-django` for automated unit and integration testing.

### Running the Test Suite
```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run tests for transactions app
python -m pytest transactions/
```

---

## 🛠️ Troubleshooting & FAQ

#### 1. `psycopg2.OperationalError: connection to server at localhost failed`
- Verify PostgreSQL service is running: `Get-Service -Name *postgres*` (Windows) or `systemctl status postgresql` (Linux).
- Check `DB_USER` and `DB_PASSWORD` in your local `.env` file.

#### 2. `ModuleNotFoundError: No module named 'dotenv'`
- Ensure virtual environment is activated and dependencies are installed: `pip install -r requirements.txt`.

---

## 📐 Code Quality & Git Standards

- **Commit Message Convention**: All commit messages follow standard Imperative Present Tense (e.g., `Implement custom user model foundation`, `Add PostgreSQL database configuration`).
- **Single Responsibility Commits**: Each commit represents a distinct, logical development step without combining unrelated changes.
- **PEP 8 Compliance**: Code formatted according to standard Python style guidelines.

---

## 📂 Project Structure

```text
FinTrack/
├── .env.example               # Example environment variable file
├── .gitignore                  # Git ignore rules for Python/Django/PostgreSQL
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation & roadmap
├── authentication/             # JWT Authentication application module
│   ├── __init__.py
│   ├── apps.py                 # App configuration
│   ├── permissions.py          # DRF permission rules
│   ├── serializers.py          # Registration & UserProfile serializers
│   ├── urls.py                 # Auth endpoints routing
│   ├── views.py                # Register, Logout & Profile views
│   └── tests/                  # Authentication test suite
│       ├── __init__.py
│       └── test_authentication.py
├── finance_tracker/            # Main Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py            # Project settings & JWT config
│   ├── urls.py                # Main URL configuration
│   └── wsgi.py
├── transactions/               # Category & Transaction management module
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── choices.py
│   ├── filters.py             # Advanced transaction filters & validation
│   ├── migrations/
│   ├── models.py              # Category & Transaction models
│   ├── pagination.py          # DRF Pagination configuration
│   ├── permissions.py         # DRF IsOwner permission class
│   ├── serializers.py         # Category & Transaction serializers
│   ├── urls.py                # Categories & Transactions routes
│   ├── views.py                # Category & Transaction views
│   └── tests/                  # Category & Transaction test suite
└── users/                      # User management application module
    ├── __init__.py
    ├── admin.py                # CustomUserAdmin configuration
    ├── apps.py                 # App configuration
    ├── models.py               # Custom User model (AbstractUser)
    ├── tests.py                # User model unit test suite
    ├── urls.py                 # Users module routes
    └── views.py                # Users module views
```

---

## 📄 License
MIT License
