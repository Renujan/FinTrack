# Personal Finance Tracker SaaS - Backend

A scalable, secure Personal Finance Tracker SaaS backend application built with **Django REST Framework (DRF)** and **PostgreSQL**.

---

## 🏗️ Architecture Overview

The system follows clean modular monolithic architecture designed for SaaS scalability:
- **Custom Authentication Layer**: Built on top of Django's `AbstractUser` to support flexible multi-currency financial profiles and SimpleJWT authentication.
- **Database Architecture**: Powered by PostgreSQL for relational data integrity, transactional safety, and index-optimized query performance.
- **RESTful API Infrastructure**: Built with Django REST Framework (DRF) preparing standard JSON endpoints for React frontend integration.
- **Security & Data Isolation**: Strict user-level queryset isolation preventing IDOR attacks, object-level permission enforcement, and DRF rate limiting.
- **Production Readiness**: Environment isolation via `python-dotenv`, production security headers, structured backend logging, and health-check monitoring.

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
- [x] **Day 5**: Backend API Layer & Quality Enhancements (Custom DRF exception handling, standardized API error formatting, category validation, transaction validation, category & transaction filtering, search, ordering, pagination, and integration tests).
- [x] **Day 6**: Backend Security, Performance & Production Readiness (Authentication hardening, strict permission enforcement, user data isolation/IDOR protection, database query optimization with `select_related`, database indexing, API rate limiting/throttling, production configuration & security headers, structured logging, health check endpoint, comprehensive tests).
- [x] **Day 7**: Budget Management & Financial Limits (Budget model, category vs overall budgets, period validation, spending calculation service, transaction integration, filtering, search, ordering, pagination, comprehensive tests, 14 Git commits).


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
| `JWT_ACCESS_MINUTES` | `60` | JWT access token expiration lifetime in minutes |
| `JWT_REFRESH_DAYS` | `1` | JWT refresh token expiration lifetime in days |
| `THROTTLE_ANON_RATE` | `30/minute` | Rate limit for unauthenticated API requests |
| `THROTTLE_USER_RATE` | `100/minute` | Rate limit for authenticated API requests |
| `SECURE_SSL_REDIRECT` | `False` | Force SSL redirection in production |
| `SESSION_COOKIE_SECURE` | `False` | Secure flag for session cookies |
| `CSRF_COOKIE_SECURE` | `False` | Secure flag for CSRF cookies |
| `LOG_LEVEL` | `INFO` | Backend logger verbosity level |

---

## 🩺 System Health Check API

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/health/` | No | Operational status & database connectivity check |

### Response Example (`200 OK`):
```json
{
  "status": "healthy",
  "database": "connected"
}
```

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

---

## 🛡️ Security, Data Isolation & Performance Improvements (Day 6)

### 1. User Data Isolation & IDOR Protection
- All `Category` and `Transaction` querysets are scoped to `user=request.user`.
- Accessing another user's resource ID returns `404 Not Found`, preventing object ID enumeration and unauthorized data modification/deletion.
- Category cross-user references during transaction creation are blocked with explicit validation.

### 2. Query Optimization
- `Transaction` list and detail querysets use `.select_related('category')` to eliminate N+1 queries during serialization of category names.

### 3. Database Indexing
- Performance indexes added:
  - `idx_cat_user_name` on `Category(user, name)`
  - `idx_txn_user_amount` on `Transaction(user, amount)`
  - `idx_txn_user_created` on `Transaction(user, created_at)`
  - Existing index `idx_txn_user_date`, `idx_txn_user_type`, `idx_txn_user_category`

### 4. Throttling & Rate Limiting
- DRF throttling enabled:
  - Anonymous users: `30 requests/minute` (`AnonRateThrottle`)
  - Authenticated users: `100 requests/minute` (`UserRateThrottle`)

### 5. Production Security Headers
- `X-Frame-Options: DENY` (clickjacking protection)
- `X-Content-Type-Options: nosniff` (MIME sniffing protection)
- `SECURE_BROWSER_XSS_FILTER = True`

---

## 🧪 Testing Guide

We use `pytest` and `pytest-django` for automated unit and integration testing.

### Running the Test Suite
```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run Day 6 security and performance test suite
python -m pytest transactions/tests/test_day6_security_perf.py
```

### Test Suite Results Summary
- Total tests: **104**
- Passed: **104**
- Failed: **0**

---

## 📄 License
MIT License
