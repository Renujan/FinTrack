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
- [x] **Day 8**: Financial Analytics & Summary APIs (Dashboard financial summary, income/expense totals, net balance, transaction counts, category spending breakdown, income/expense trends, date-range analytics, monthly summaries, daily/weekly/monthly trends, top spending categories, period comparison, budget analytics integration, user data isolation, 156 total automated tests, 14 Git commits).
- [x] **Day 9**: Recurring Transactions & Scheduled Finance Operations (RecurringTransaction model, daily/weekly/monthly/yearly recurrence choices, schedule date validation, user ownership, CRUD API, pause/resume endpoints, transaction generation service, scheduled management command, duplicate protection, filtering, search, ordering, pagination, budget & analytics integration, 177 total automated tests, 13 Git commits).
- [x] **Day 10**: Financial Goals & Savings Targets (FinancialGoal model, target amount & date, goal progress calculation service, income transaction contributions, dynamic status logic (ACTIVE, COMPLETED, OVERDUE, PAUSED), CRUD API, pause/resume endpoints, user ownership isolation, filtering, search, ordering, pagination, 204 total automated tests, 12 Git commits).

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

## 🎯 Budget Management API Documentation (Day 7)

Base URL: `/api/`

All Budget endpoints require `Authorization: Bearer <access_token>` header.

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/budgets/` | Yes (`Bearer`) | List, search, filter, sort, and paginate budgets |
| `POST` | `/api/budgets/` | Yes (`Bearer`) | Create a category or overall budget |
| `GET` | `/api/budgets/<id>/` | Yes (`Bearer`) | Retrieve budget details with calculated metrics |
| `PUT` | `/api/budgets/<id>/` | Yes (`Bearer`) | Full update of budget parameters |
| `PATCH` | `/api/budgets/<id>/` | Yes (`Bearer`) | Partial update of budget parameters |
| `DELETE` | `/api/budgets/<id>/` | Yes (`Bearer`) | Delete a budget |

### 💡 Category vs. Overall Budgets
- **Category Budget**: Set `category` to a valid category ID owned by the user. Only expense transactions for that specific category within the budget date range are counted toward spending.
- **Overall Budget**: Set `category` to `null`. All expense transactions for the user within the budget date range are aggregated across all categories.

### 📅 Supported Budget Periods
- `WEEKLY`: Weekly budget cycle
- `MONTHLY`: Monthly budget cycle
- `CUSTOM`: Custom date range budget

### 🧮 Budget Calculation & Metrics
For each budget, the calculation engine dynamically evaluates matching `EXPENSE` transactions in the date range `[start_date, end_date]`:
- `spent_amount`: Total sum of expenses matching budget scope and date window.
- `remaining_amount`: `amount - spent_amount`
- `percentage_used`: `(spent_amount / amount) * 100` (rounded to 2 decimal places).
- `is_exceeded`: `True` if `spent_amount > amount`, `False` otherwise.

### Response Example (`200 OK` / `201 Created`):
```json
{
  "id": 1,
  "name": "August Dining Out",
  "category": 3,
  "category_name": "Dining Out",
  "is_overall": false,
  "amount": "500.00",
  "budget_amount": "500.00",
  "period": "MONTHLY",
  "start_date": "2026-08-01",
  "end_date": "2026-08-31",
  "spent_amount": "350.00",
  "remaining_amount": "150.00",
  "percentage_used": 70.0,
  "is_exceeded": false,
  "created_at": "2026-08-16T09:00:00Z",
  "updated_at": "2026-08-16T09:00:00Z"
}
```

### 🛡️ Validation Rules
- **Amount**: Must be positive (`> 0.00`).
- **Dates**: `start_date` and `end_date` are required. `end_date` must not be before `start_date`.
- **Category**: Optional. If provided, category must belong to the authenticated request user.
- **Period**: Must be one of `WEEKLY`, `MONTHLY`, `CUSTOM`.

---

## 📊 Financial Analytics & Summary API Documentation (Day 8)

Base URL: `/api/analytics/`

All Analytics endpoints require `Authorization: Bearer <access_token>` header.

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/analytics/summary/` | Yes (`Bearer`) | Dashboard overall financial summary (income, expenses, net balance, counts, averages) |
| `GET` | `/api/analytics/trends/` | Yes (`Bearer`) | Financial trends grouped by period (`daily`, `weekly`, `monthly`) |
| `GET` | `/api/analytics/monthly/` | Yes (`Bearer`) | Monthly financial summaries ordered chronologically |
| `GET` | `/api/analytics/categories/` | Yes (`Bearer`) | Category spending analytics for expense transactions (supports `limit` param) |
| `GET` | `/api/analytics/comparison/` | Yes (`Bearer`) | Period comparison against previous comparable period with percentage changes |
| `GET` | `/api/analytics/budgets/` | Yes (`Bearer`) | Budget analytics integration (active, exceeded, total budgeted, total spending, utilization) |

### 📅 Date Range Filtering Across Analytics
All analytics endpoints support optional date filtering query parameters:
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`

**Validation**:
- Format must strictly follow `YYYY-MM-DD`.
- `start_date` must be less than or equal to `end_date`.
- Returns `400 Bad Request` with structured DRF validation error if parameters are invalid.

### 📈 Financial Trends Grouping
The `/api/analytics/trends/` endpoint supports grouping via `group_by` query parameter:
- `daily`: Group trends by day (`YYYY-MM-DD`)
- `weekly`: Group trends by week start date (`YYYY-MM-DD`)
- `monthly`: Group trends by month (`YYYY-MM`) (Default)

### 🏷️ Category Analytics & Top Spending Categories
The `/api/analytics/categories/` endpoint aggregates expense spending by category:
- `limit`: Optional positive integer (1 to 100) to return top spending categories ordered by total amount spent descending.
- Calculates spending, transaction count, and `percentage_of_total` spending.

### 🔄 Period Comparison Calculation
The `/api/analytics/comparison/` endpoint compares the selected period against an immediately preceding period of equal duration:
- Computes percentage changes (`income_change`, `expense_change`, `net_change`).
- Handles zero previous values safely without division by zero errors.

### 💰 Budget Analytics Integration
The `/api/analytics/budgets/` endpoint integrates Day 7 budget calculation logic:
- Evaluates active budgets, exceeded budgets, total budgeted amount, total spent across budgets, and overall utilization rate.

---

## 🔄 Recurring Transactions & Scheduled Operations API Documentation (Day 9)

Base URL: `/api/recurring-transactions/`

All Recurring Transaction endpoints require `Authorization: Bearer <access_token>` header.

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/recurring-transactions/` | Yes (`Bearer`) | List, search, filter, sort, and paginate recurring transaction schedules |
| `POST` | `/api/recurring-transactions/` | Yes (`Bearer`) | Create a new recurring income or expense schedule |
| `GET` | `/api/recurring-transactions/<id>/` | Yes (`Bearer`) | Retrieve recurring transaction schedule details |
| `PUT` | `/api/recurring-transactions/<id>/` | Yes (`Bearer`) | Full update of a recurring transaction schedule |
| `PATCH` | `/api/recurring-transactions/<id>/` | Yes (`Bearer`) | Partial update of a recurring transaction schedule |
| `DELETE` | `/api/recurring-transactions/<id>/` | Yes (`Bearer`) | Delete a recurring transaction schedule |
| `POST` | `/api/recurring-transactions/<id>/pause/` | Yes (`Bearer`) | Pause an active schedule (`is_active = False`) |
| `POST` | `/api/recurring-transactions/<id>/resume/` | Yes (`Bearer`) | Resume a paused schedule (`is_active = True`) |

### 🗓️ Recurrence Frequencies & Next Occurrence Calculation
- `DAILY`: Advances by 1 day.
- `WEEKLY`: Advances by 7 days.
- `MONTHLY`: Advances by 1 month, handling month-end boundaries (e.g. Jan 31 -> Feb 28/29).
- `YEARLY`: Advances by 1 year, handling leap year edge cases (e.g. Feb 29 -> Feb 28 in non-leap year).

### ⚙️ Scheduled Transaction Generation
- **Management Command**: `python manage.py process_recurring_transactions [--date YYYY-MM-DD]`
- **Generation Service**: `RecurringTransactionService.process_due_recurring_transactions(target_date)`
- Scans active schedules where `next_run_date <= target_date`, generates `Transaction` records, updates `last_run_date`, computes `next_run_date`, and deactivates expired schedules (`end_date`).

### 🛡️ Duplicate Prevention & Idempotency
- Uses a unique database constraint `unique_recurring_occurrence` on `Transaction(recurring_transaction, recurring_schedule_date)`.
- Re-running the generation service or management command multiple times on the same date is 100% idempotent and safe.

---

## 🛡️ Security, Data Isolation & Performance Improvements (Day 6)

### 1. User Data Isolation & IDOR Protection
- All `Category`, `Transaction`, `Budget`, and `RecurringTransaction` querysets are scoped to `user=request.user`.
- Accessing another user's resource ID returns `404 Not Found`, preventing object ID enumeration and unauthorized data modification/deletion.
- Category cross-user references during creation are blocked with explicit validation.

### 2. Query Optimization
- `Transaction` list and detail querysets use `.select_related('category')` to eliminate N+1 queries during serialization of category names.
- `Budget` list and detail querysets use `.select_related('category')` to optimize database performance.
- `RecurringTransaction` querysets use `.select_related('category')` to optimize database query speed.

### 3. Database Indexing
- Performance indexes added:
  - `idx_cat_user_name` on `Category(user, name)`
  - `idx_txn_user_amount` on `Transaction(user, amount)`
  - `idx_txn_user_created` on `Transaction(user, created_at)`
  - `idx_budget_user_dates` on `Budget(user, start_date, end_date)`
  - `idx_budget_user_category` on `Budget(user, category)`
  - `idx_budget_user_period` on `Budget(user, period)`
  - `idx_rec_user_act_next` on `RecurringTransaction(user, is_active, next_run_date)`
  - `idx_rec_user_category` on `RecurringTransaction(user, category)`
  - `idx_rec_user_type` on `RecurringTransaction(user, transaction_type)`
  - `idx_rec_user_freq` on `RecurringTransaction(user, frequency)`

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

# Run Day 9 recurring transaction test suite specifically
python -m pytest transactions/tests/test_recurring_transactions.py
```

### Test Suite Results Summary
- Total tests: **177**
- Passed: **177**
- Failed: **0**


---

## 📄 License
MIT License

