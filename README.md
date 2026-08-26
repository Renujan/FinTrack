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
- [x] **Day 11**: Notifications & Financial Alerts (Notification model, notification choices, NotificationService, budget warning/exceeded alerts, goal warning/completed alerts, recurring transaction due/generated/expired alerts, duplicate protection, read/unread state management, list/retrieve/update/delete API endpoints, mark-all-read endpoint, filtering, search, pagination, process_financial_notifications management command, 222 total automated tests, 13 Git commits).
- [x] **Day 12**: Data Export, Import & Financial Reports (Financial data export services, transaction CSV export with filters, categories/budgets/goals/recurring CSV exports, unified financial reports API, date range filtering, transaction CSV import with strict row validation, cross-user category protection, row fingerprint duplicate import protection, security & file handling, 249 total automated tests, 12 Git commits).
- [x] **Day 13**: API Security, Rate Limiting, Audit Logs & Production Hardening (JWT auth hardening, permission enforcement, IDOR protection, centralized rate throttling for auth/analytics/imports, AuditLog model & AuditLogService, audit trail APIs (/api/audit-logs/), audit hooks across CRUD/auth/import operations, error response sanitization, import file size/row limits, SECURITY.md guide, production Django checks, 269 total automated tests, 13 Git commits).
- [x] **Day 14**: Subscription Plans, Tier Limits & Usage Tracking (SubscriptionPlan & UserSubscription models, FREE/PREMIUM/PRO/ENTERPRISE tiers, usage tracking service, limit enforcement on transactions, categories, budgets, recurring items, and goals, subscription detail, plans list, usage, upgrade, and cancel APIs, 290 total automated tests, 13 Git commits).
- [x] **Day 15**: API Documentation, OpenAPI & Developer Experience (OpenAPI 3.0 schema generation via `drf-spectacular`, interactive Swagger UI at `/api/docs/`, ReDoc reference at `/api/redoc/`, raw OpenAPI schema at `/api/schema/`, `@extend_schema` annotations, versioning readiness at `/api/v1/`, complete developer guide in `API.md`, 13 Git commits).
- [x] **Day 16**: Backend Code Audit, Error Fixing & Refactoring (Complete backend audit, Python compilation and import verification, Django configuration checks, permission & user data isolation audit, serializer validation cleanup, OpenAPI schema generator warning resolutions, service layer refactoring, error handler standardization, project cleanup, manual API verification, 12 Git commits).
- [x] **Day 17**: Financial Reports & Advanced Reporting API (ReportService foundation, income reports, expense reports, cash-flow summary & savings rate, category spending breakdown, monthly aggregation, spending trends, budget vs actual comparison, top spending categories with limit validation, query parameter filters & validation, 8 dedicated read-only REST API endpoints under /api/reports/, OpenAPI annotations, documentation, 12 Git commits).

---

## 📖 API Documentation & OpenAPI Specification (Day 15)

The SaaS Finance Tracker provides complete interactive and reference API documentation:

- **Swagger UI**: [`/api/docs/`](http://127.0.0.1:8000/api/docs/) — Interactive API testing and parameter inspection.
- **ReDoc**: [`/api/redoc/`](http://127.0.0.1:8000/api/redoc/) — Clean 3-panel API reference.
- **OpenAPI Schema**: [`/api/schema/`](http://127.0.0.1:8000/api/schema/) — Raw OpenAPI 3.0 specification (YAML/JSON).
- **Developer Guide**: Refer to [`API.md`](file:///c:/Users/Renu/Desktop/git_plan/API.md) for full integration architecture, environment setup, JWT headers, filtering options, status codes, and endpoint payloads.

---


## 📤 Data Export, Import & Financial Reporting API Documentation (Day 12)

Base URL: `/api/`

All Export, Import, and Reporting endpoints require `Authorization: Bearer <access_token>` header.

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/export/transactions/` | Yes (`Bearer`) | Export user's transactions as CSV (supports filtering & search) |
| `GET` | `/api/export/categories/` | Yes (`Bearer`) | Export user's categories list as CSV |
| `GET` | `/api/export/budgets/` | Yes (`Bearer`) | Export user's budgets with calculation metrics as CSV |
| `GET` | `/api/export/goals/` | Yes (`Bearer`) | Export user's financial goals with progress metrics as CSV |
| `GET` | `/api/export/recurring/` | Yes (`Bearer`) | Export user's recurring transaction schedules as CSV |
| `GET` | `/api/reports/financial/` | Yes (`Bearer`) | Unified financial report JSON (income, expenses, net balance, breakdowns) |
| `POST` | `/api/import/transactions/` | Yes (`Bearer`) | Import transaction records from uploaded CSV file |

### 📤 1. CSV Data Exports
- **Transaction Export Filters**: Supports `start_date`, `end_date`, `category`, `type` (`INCOME`/`EXPENSE`), `min_amount`, `max_amount`, `search`/`q`.
- **Response Headers**: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="<type>_export.csv"`.
- **CSV Headers**:
  - Transactions: `Date,Description,Amount,Transaction Type,Category,Created Date`
  - Categories: `ID,Name,Created At,Updated At`
  - Budgets: `ID,Name,Category,Amount,Period,Start Date,End Date,Spent Amount,Remaining Amount,Percentage Used,Is Exceeded,Created At`
  - Goals: `ID,Name,Description,Category,Target Amount,Target Date,Current Amount,Remaining Amount,Percentage Complete,Status,Is Active,Created At`
  - Recurring: `ID,Name,Description,Amount,Transaction Type,Category,Frequency,Start Date,End Date,Next Run Date,Last Run Date,Is Active,Created At`

### 📊 2. Financial Report API (`GET /api/reports/financial/`)
- Accepts optional `start_date` and `end_date` parameters (`YYYY-MM-DD`).
- **Response Metrics**:
  - `total_income`, `total_expenses`, `net_balance`, `transaction_count`
  - `top_spending_categories`: Top 5 spending categories by expense amount.
  - `category_spending_breakdown`: Full category expense breakdown with percentages.
  - `monthly_totals`: Chronological monthly totals.
  - `budget_summary`: Total budgets, active/exceeded counts, total budgeted, total spent, utilization %.
  - `goal_summary`: Total goals, active/completed counts, total target, total saved, progress %.

### 📥 3. Transaction CSV Import (`POST /api/import/transactions/`)
- **Uploaded File**: Multipart form upload (`file` or `csv_file` field). Max size: **5MB**. Supported format: `.csv`.
- **Supported CSV Columns**: `date`, `description`, `amount`, `transaction_type`, `category` (case-insensitive headers).
- **Validation Rules**:
  - `date`: Valid `YYYY-MM-DD` date.
  - `amount`: Decimal strictly `> 0.00`.
  - `transaction_type`: `INCOME` or `EXPENSE`.
  - `category`: Must match an existing category ID or name owned by the authenticated user.
- **Duplicate Protection**:
  - Computes a SHA-256 fingerprint (`user_id`, `date`, `amount`, `transaction_type`, `category_id`, `description`).
  - Blocks duplicate rows within the same uploaded CSV file.
  - Checks database to prevent re-importing existing duplicate transactions.
- **Response Format**:
```json
{
  "success": true,
  "imported": 18,
  "failed": 0,
  "errors": []
}
```
If errors occur on specific rows:
```json
{
  "success": false,
  "imported": 16,
  "failed": 2,
  "errors": [
    {
      "row": 5,
      "field": "amount",
      "message": "Amount must be greater than zero."
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

# Run Day 12 export/import/report test suite specifically
python -m pytest transactions/tests/test_export_import.py
```

### Test Suite Results Summary
- Total tests: **249**
- Passed: **249**
- Failed: **0**


---

## 📄 License
MIT License


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

## 🎯 Financial Goals & Savings Targets API Documentation (Day 10)

Base URL: `/api/goals/`

All Financial Goal endpoints require `Authorization: Bearer <access_token>` header.

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/goals/` | Yes (`Bearer`) | List, search, filter, sort, and paginate financial goals |
| `POST` | `/api/goals/` | Yes (`Bearer`) | Create a new financial goal |
| `GET` | `/api/goals/<id>/` | Yes (`Bearer`) | Retrieve financial goal details with progress metrics |
| `PUT` | `/api/goals/<id>/` | Yes (`Bearer`) | Full update of a financial goal |
| `PATCH` | `/api/goals/<id>/` | Yes (`Bearer`) | Partial update of a financial goal |
| `DELETE` | `/api/goals/<id>/` | Yes (`Bearer`) | Delete a financial goal |
| `POST` | `/api/goals/<id>/pause/` | Yes (`Bearer`) | Pause an active goal (`is_active = False`) |
| `POST` | `/api/goals/<id>/resume/` | Yes (`Bearer`) | Resume a paused goal (`is_active = True`) |

### 💰 Progress Calculation & Contribution Rules
Goal metrics are computed dynamically via `GoalCalculationService`:
- **Contributions**: `INCOME` transactions belonging to `goal.user` with `date <= target_date`.
- **Category Filter**: If `goal.category` is set, contributions are restricted to that specific category.
- `current_amount`: Sum of eligible income transactions.
- `remaining_amount`: `max(0, target_amount - current_amount)`.
- `percentage_complete`: `(current_amount / target_amount) * 100` (rounded to 2 decimal places).
- `is_completed`: `current_amount >= target_amount`.

### 📊 Dynamic Goal Statuses
- `COMPLETED`: Calculated when `current_amount >= target_amount`.
- `PAUSED`: Set when `is_active = False`.
- `OVERDUE`: Evaluated when `target_date < today` and not completed and active.
- `ACTIVE`: Evaluated when `target_date >= today` and not completed and active.

### Response Example (`200 OK` / `201 Created`):
```json
{
  "id": 1,
  "name": "Emergency Savings",
  "description": "6 months of living expenses",
  "category": 2,
  "category_name": "Savings",
  "target_amount": "5000.00",
  "target_date": "2026-12-31",
  "is_active": true,
  "current_amount": "3250.00",
  "remaining_amount": "1750.00",
  "percentage_complete": 65.0,
  "is_completed": false,
  "status": "ACTIVE",
  "created_at": "2026-08-19T10:00:00Z",
  "updated_at": "2026-08-19T10:00:00Z"
}
```

---

## 🛡️ Security, Data Isolation & Performance Improvements (Day 6 - Day 10)

### 1. User Data Isolation & IDOR Protection
- All `Category`, `Transaction`, `Budget`, `RecurringTransaction`, and `FinancialGoal` querysets are scoped to `user=request.user`.
- Accessing another user's resource ID returns `404 Not Found`, preventing object ID enumeration and unauthorized data modification/deletion.
- Category cross-user references during creation are blocked with explicit validation.

### 2. Query Optimization
- `Transaction` list and detail querysets use `.select_related('category')` to eliminate N+1 queries during serialization of category names.
- `Budget` list and detail querysets use `.select_related('category')` to optimize database performance.
- `RecurringTransaction` querysets use `.select_related('category')` to optimize database query speed.
- `FinancialGoal` querysets use `.select_related('category')` to eliminate N+1 database queries.

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
  - `idx_goal_user_target_date` on `FinancialGoal(user, target_date)`
  - `idx_goal_user_category` on `FinancialGoal(user, category)`
  - `idx_goal_user_is_active` on `FinancialGoal(user, is_active)`
  - `idx_notif_user_is_read` on `Notification(user, is_read)`
  - `idx_notif_user_type` on `Notification(user, notification_type)`
  - `idx_notif_user_created` on `Notification(user, created_at)`

### 4. Throttling & Rate Limiting
- DRF throttling enabled:
  - Anonymous users: `30 requests/minute` (`AnonRateThrottle`)
  - Authenticated users: `100 requests/minute` (`UserRateThrottle`)

### 5. Production Security Headers
- `X-Frame-Options: DENY` (clickjacking protection)
- `X-Content-Type-Options: nosniff` (MIME sniffing protection)
- `SECURE_BROWSER_XSS_FILTER = True`

---

## 🔔 Notifications & Financial Alerts Architecture (Day 11)

### 1. Notification Model & Choices
The `Notification` model provides user-isolated alerts:
- `user`: Authenticated owner.
- `notification_type`: One of:
  - `BUDGET_EXCEEDED`
  - `BUDGET_WARNING`
  - `GOAL_COMPLETED`
  - `GOAL_WARNING`
  - `RECURRING_DUE`
  - `RECURRING_GENERATED`
  - `RECURRING_EXPIRED`
- `title` & `message`: Human-readable summary text.
- `is_read` & `read_at`: Status tracking (`is_read=True` sets timestamp `read_at=now()`).
- `metadata`: JSON payload containing context references (`budget_id`, `goal_id`, `recurring_transaction_id`, etc.).

### 2. Alert Rules & Thresholds
- **Budget Alerts**:
  - `BUDGET_WARNING`: Triggered when expense spending reaches 80% or more of budget limit.
  - `BUDGET_EXCEEDED`: Triggered when expense spending exceeds 100% of budget limit.
- **Financial Goal Alerts**:
  - `GOAL_WARNING`: Triggered when saved income reaches 80% or more of goal target amount.
  - `GOAL_COMPLETED`: Triggered when saved income reaches or exceeds 100% of target amount.
- **Recurring Transaction Alerts**:
  - `RECURRING_DUE`: Triggered for active schedules approaching their next run date.
  - `RECURRING_GENERATED`: Triggered automatically when a transaction is generated for a schedule.
  - `RECURRING_EXPIRED`: Triggered when a recurring schedule reaches its end date.

### 3. Service Layer & Duplicate Prevention
- `NotificationService` handles notification generation with built-in metadata-level duplicate protection:
  - Budget warnings/exceeded alerts check for existing notifications per budget and period.
  - Goal alerts check for existing notifications per goal milestone.
  - Recurring alerts check for existing notifications per schedule occurrence/event.
  - Paused recurring transaction schedules (`is_active=False`) are automatically skipped for due alerts.

### 4. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notifications/` | List notifications (search, filter, pagination, ordering) |
| `GET` | `/api/notifications/<id>/` | Retrieve notification detail |
| `PATCH` | `/api/notifications/<id>/` | Mark single notification as read/unread |
| `DELETE` | `/api/notifications/<id>/` | Delete single notification |
| `POST` | `/api/notifications/mark-all-read/` | Bulk mark all user notifications as read |

### 5. Automated Financial Processing Command
Execute financial alert checking across budgets, goals, and recurring transactions:
```bash
python manage.py process_financial_notifications
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

# Run Day 11 notifications test suite specifically
python -m pytest transactions/tests/test_notifications.py
```

### Test Suite Results Summary
- Total tests: **269**
- Passed: **269**
- Failed: **0**




---

## 💳 Day 14 — SaaS Subscription & Plan Management

Day 14 builds the foundation for SaaS Subscription & Plan Management in the Django REST Framework backend.

> [!NOTE]
> Payment gateway integration (e.g. Stripe) is intentionally not implemented in Day 14. Plan transitions and state changes represent safe backend business-logic operations.

### 1. Subscription Models & Architecture
- **`SubscriptionPlan`**:
  - Defines available tiers (`free`, `premium`, custom plans).
  - Pricing (Decimal), billing period (`MONTHLY`, `YEARLY`), and feature flags JSON.
  - Configurable limits: `max_transactions`, `max_budgets`, `max_goals`, `max_categories`, `max_recurring_transactions`, `max_import_size` (`-1` for unlimited).
- **`UserSubscription`**:
  - One-to-one user relationship ensuring no conflicting active subscriptions per user.
  - Status tracking: `ACTIVE`, `TRIAL`, `EXPIRED`, `CANCELLED`.
  - Expiration detection: dynamic calculation based on `end_date` vs current timestamp.

### 2. Default Free Plan & Auto-Provisioning
- Default **Free Plan** parameters:
  - Transactions: 500 / month
  - Budgets: 5
  - Financial Goals: 3
  - Categories: 20
  - Recurring Transactions: 5
  - Max CSV Import Rows: 100
- Users without an explicit subscription are automatically provisioned with a default Free Plan subscription upon request.

### 3. Usage Calculation & Access Control Service
- `SubscriptionService` centralizes usage tracking and limit checking:
  - `get_usage(user)`: Returns current usage vs plan limits.
  - `check_limit(user, limit_type)`: Enforces limits on transactions, budgets, goals, categories, recurring rules, and imports.
  - When a user exceeds a limit, a HTTP `403 Forbidden` response is returned with code `PLAN_LIMIT_REACHED`.
  - Example error payload:
    ```json
    {
        "detail": "Plan limit reached for transactions. Current usage: 500, Maximum allowed: 500.",
        "error_code": "PLAN_LIMIT_REACHED",
        "limit_type": "transactions",
        "current_usage": 500,
        "max_allowed": 500,
        "upgrade_suggestion": "Please upgrade your subscription plan to increase your resource limits."
    }
    ```

### 4. Subscription API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/subscription/` | Get current user's subscription details |
| `GET` | `/api/subscription/usage/` | Get usage counts vs. plan limits |
| `GET` | `/api/subscription/plans/` | List all available active subscription plans |
| `POST` | `/api/subscription/upgrade/` | Upgrade/change user plan (e.g. `{"plan_code": "premium"}`) |
| `POST` | `/api/subscription/cancel/` | Cancel user subscription (sets `auto_renew=False`) |

### 5. Plan Transitions & Data Integrity
- Upgrading to Premium immediately increases plan limits.
- Downgrading to Free preserves all pre-existing user data. No data is deleted upon downgrade; creation of new resources is blocked if usage exceeds new plan limits.

### 6. Architecture & Limits Summary
- **Database Limits**: Enforced dynamically per user subscription plan fetched from database models (no hardcoded limits).
- **Concurrency & Isolation**: One active subscription per user; cross-tenant modification prevented by DRF user-ownership scoping.


---

## 🧹 Day 16 — Backend Code Audit, Error Fixing & Refactoring

Complete backend quality audit, error fixing, and refactoring executed with non-test verification suite and 12 Git commits.

### Key Audit & Refactoring Accomplishments:
1. **OpenAPI & DRF Schema Generator Fixes**: Resolved all `drf_spectacular.W002` schema generator warnings by adding explicit `@extend_schema(request=None)` annotations to action-only views (`FinancialGoalPauseView`, `FinancialGoalResumeView`, `NotificationMarkAllReadView`, `RecurringTransactionPauseView`, `RecurringTransactionResumeView`, `SubscriptionCancelView`).
2. **Exception Handling Standardization**: Refined `custom_exception_handler` in `finance_tracker/exceptions.py` to standardize error formatting across 400, 401, 403, 404, 409, 429, and 500 status codes.
3. **Authentication & Permissions Hardening**: Strengthened `IsOwner` and `IsOwnerOrReadOnly` permission checks in `transactions/permissions.py` with safe attribute getters (`getattr(obj, 'user', None)`).
4. **Serializer Validation & Ownership Checks**: Added string null/empty checks in `SubscriptionUpgradeSerializer` and verified category ownership filtering across transaction, budget, recurring, and goal serializers.
5. **Database & Query Performance**: Verified `select_related('category')` pre-fetching across transaction list, detail, and analytics querysets.
6. **Code Cleanup**: Removed unused imports (`django.shortcuts.render`) and placeholder comments across `users` and `authentication` modules.
7. **Non-Test Verification Suite**:
   - `python -m compileall .` → PASS
   - `python manage.py check` → PASS
   - `python manage.py check --deploy` → PASS
   - `python manage.py makemigrations --check` → PASS
   - `python manage.py migrate --plan` → PASS
   - Django shell API manual verification → PASS (11 core API suites verified)

---

## 📄 License
MIT License





