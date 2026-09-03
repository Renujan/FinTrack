# SaaS Finance Tracker — API & Developer Integration Guide

Welcome to the **SaaS Finance Tracker API Documentation**. This guide provides complete details for frontend developers, mobile engineers, and integration partners on consuming the backend RESTful API.

---

## 🚀 Architecture & Base URLs

The backend is built with **Django 5** and **Django REST Framework (DRF)** using PostgreSQL for relational data storage and JWT (JSON Web Tokens) for authentication.

- **Local Base URL**: `http://127.0.0.1:8000/api/`
- **API Version 1 Alias**: `http://127.0.0.1:8000/api/v1/`

---

## 📚 OpenAPI & Interactive Documentation

The backend provides automatically generated OpenAPI 3.0 schemas and interactive documentation interfaces:

- **Swagger UI (Interactive API Explorer)**: [`/api/docs/`](http://127.0.0.1:8000/api/docs/)
- **ReDoc (Reference Documentation)**: [`/api/redoc/`](http://127.0.0.1:8000/api/redoc/)
- **Raw OpenAPI Schema (YAML/JSON)**: [`/api/schema/`](http://127.0.0.1:8000/api/schema/) (Append `?format=json` for JSON output)
- **Day 16 Schema Verification**: All action APIViews (`/api/goals/{id}/pause/`, `/api/goals/{id}/resume/`, `/api/recurring-transactions/{id}/pause/`, `/api/recurring-transactions/{id}/resume/`, `/api/notifications/mark-all-read/`, `/api/subscription/cancel/`) feature explicit OpenAPI `@extend_schema(request=None)` schema definitions.

---

## 🔑 Authentication Flow

The API uses **JWT (JSON Web Tokens)** for stateless authentication.

### 1. Register Account
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "StrongPassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "currency": "USD"
}
```

### 2. Login (Obtain Tokens)
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "StrongPassword123!"
}
```
**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Authenticated Request Header
Pass the `access` token in the `Authorization` header for all protected endpoints:
```http
Authorization: Bearer <access_token>
```

### 4. Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

### 5. Logout (Blacklist Token)
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

---

## 🛠 Endpoint Overview

### 👤 Authentication (`/api/auth/`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | Register new user account |
| `POST` | `/api/auth/login/` | Obtain access and refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token |
| `POST` | `/api/auth/logout/` | Blacklist refresh token |
| `GET/PUT/PATCH` | `/api/auth/profile/` | Retrieve or update user profile |

### 🏷 Categories (`/api/categories/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories/` | List categories (`?search=Food&ordering=name`) |
| `POST` | `/api/categories/` | Create a new custom category |
| `GET` | `/api/categories/{id}/` | Retrieve category details |
| `PUT/PATCH` | `/api/categories/{id}/` | Update category details |
| `DELETE` | `/api/categories/{id}/` | Delete category (blocked if transactions exist) |

### 💳 Transactions (`/api/transactions/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/transactions/` | List transactions with filters (`page`, `page_size`, `search`, `category`, `transaction_type`, `start_date`, `end_date`, `min_amount`, `max_amount`, `ordering`) |
| `POST` | `/api/transactions/` | Create a new income/expense transaction |
| `GET` | `/api/transactions/{id}/` | Retrieve transaction details |
| `PUT/PATCH` | `/api/transactions/{id}/` | Update transaction |
| `DELETE` | `/api/transactions/{id}/` | Delete transaction |

### 📊 Budgets (`/api/budgets/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/budgets/` | List budgets with real-time percentage used calculations |
| `POST` | `/api/budgets/` | Create a new category budget |
| `GET` | `/api/budgets/{id}/` | Retrieve budget progress and metrics |
| `PUT/PATCH` | `/api/budgets/{id}/` | Update budget amount or date range |
| `DELETE` | `/api/budgets/{id}/` | Delete budget |

### 📈 Analytics (`/api/analytics/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary/` | Overall dashboard summary (`start_date`, `end_date`) |
| `GET` | `/api/analytics/trends/` | Financial trends (`start_date`, `end_date`, `group_by=daily/weekly/monthly`) |
| `GET` | `/api/analytics/monthly/` | Chronological monthly summary |
| `GET` | `/api/analytics/categories/` | Category spending breakdown (`limit=5`) |
| `GET` | `/api/analytics/comparison/` | Current vs previous period comparison |
| `GET` | `/api/analytics/budgets/` | Budget utilization and warning breakdown |

### 🔄 Recurring Transactions (`/api/recurring-transactions/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/recurring-transactions/` | List automated recurring schedules |
| `POST` | `/api/recurring-transactions/` | Create new recurring schedule (`daily`, `weekly`, `monthly`, `yearly`) |
| `GET/PUT/PATCH/DELETE` | `/api/recurring-transactions/{id}/` | Manage recurring schedule |
| `POST` | `/api/recurring-transactions/{id}/pause/` | Pause schedule execution |
| `POST` | `/api/recurring-transactions/{id}/resume/` | Resume paused schedule |

### 🎯 Financial Goals (`/api/goals/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/goals/` | List savings goals with completion percentage |
| `POST` | `/api/goals/` | Create financial savings goal |
| `GET/PUT/PATCH/DELETE` | `/api/goals/{id}/` | Manage financial goal |
| `POST` | `/api/goals/{id}/pause/` | Pause savings goal |
| `POST` | `/api/goals/{id}/resume/` | Resume savings goal |

### 🔔 Notifications (`/api/notifications/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notifications/` | List notifications (`is_read`, `notification_type`) |
| `GET/PATCH/DELETE` | `/api/notifications/{id}/` | Manage or mark single notification read |
| `POST` | `/api/notifications/mark-all-read/` | Mark all notifications read |

### 🛡 Audit Logs (`/api/audit-logs/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/audit-logs/` | List security audit logs (`action`, `resource_type`, `start_date`, `end_date`) |
| `GET` | `/api/audit-logs/{id}/` | Retrieve specific audit log entry |

### 📦 Import & Export (`/api/export/` & `/api/import/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/export/transactions/` | Export transactions as CSV download |
| `GET` | `/api/export/categories/` | Export categories as CSV download |
| `GET` | `/api/export/budgets/` | Export budgets as CSV download |
| `GET` | `/api/export/goals/` | Export financial goals as CSV download |
| `GET` | `/api/export/recurring/` | Export recurring schedules as CSV download |
| `POST` | `/api/import/transactions/` | Upload CSV file (`file`) for bulk transaction creation |

### 📑 Reports (`/api/reports/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/financial/` | Consolidated financial report JSON dataset |
| `GET` | `/api/reports/income/` | Income summary statistics (total, count, avg, min, max) |
| `GET` | `/api/reports/expenses/` | Expense summary statistics (total, count, avg, min, max, category/search) |
| `GET` | `/api/reports/cash-flow/` | Net cash flow & savings rate report |
| `GET` | `/api/reports/categories/` | Category expense spending breakdown & percentages |
| `GET` | `/api/reports/monthly/` | Chronological monthly aggregated income, expenses, and net balance |
| `GET` | `/api/reports/trends/` | Financial trends aggregated by daily, weekly, or monthly intervals |
| `GET` | `/api/reports/budgets/` | Budget vs actual spending comparison and exceeded status |
| `GET` | `/api/reports/top-categories/` | Top spending categories report (customizable limit 1–100) |

### 💎 Subscriptions (`/api/subscription/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/subscription/` | Current user plan details |
| `GET` | `/api/subscription/usage/` | Current quota consumption vs limits |
| `GET` | `/api/subscription/plans/` | List available subscription tiers (`FREE`, `PREMIUM`, `PRO`, `ENTERPRISE`) |
| `POST` | `/api/subscription/upgrade/` | Switch subscription plan (`{"plan_code": "PREMIUM"}`) |
| `POST` | `/api/subscription/cancel/` | Cancel subscription auto-renewal |

---

## 🔍 Pagination, Filtering & Search

### Standard Pagination
Lists return paginated JSON payloads:
```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/transactions/?page=2",
  "previous": null,
  "results": [...]
}
```
- Query Parameters: `page` (default: 1), `page_size` (default: 20, max: 100).

### Filtering & Search Parameters
- Transactions: `?search=grocery&category=2&transaction_type=expense&start_date=2026-01-01&end_date=2026-12-31&min_amount=10&max_amount=500`
- Ordering: `?ordering=-date` or `?ordering=amount`

---

## ❌ Standardized Error Format

Errors handled by the custom exception handler return standard structure:

```json
{
  "error": "Error description or field validation details",
  "code": "error_code_identifier"
}
```

### HTTP Status Code Reference
- `400 Bad Request`: Validation failure or bad payload format.
- `401 Unauthorized`: Missing, expired, or invalid JWT token.
- `403 Forbidden`: Insufficient permissions or resource ownership check failed.
- `404 Not Found`: Target resource does not exist or belong to user.
- `409 Conflict`: Business logic state conflict.
- `429 Too Many Requests`: Rate limit exceeded for IP or user.
- `500 Internal Server Error`: Unexpected server issue.

---

## 👤 User Profile & Account Settings API (Day 18)

Day 18 provides endpoints for managing user profile information, account preferences, password changes, and account overview metrics.

### 1. User Profile (`GET /api/profile/`, `PATCH /api/profile/`)
**GET Response:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "display_name": "John D.",
  "bio": "Personal finance enthusiast",
  "phone_number": "+1234567890",
  "currency": "USD",
  "profile_updated_at": "2026-08-27T10:30:00Z",
  "created_at": "2026-08-01T00:00:00Z"
}
```

### 2. User Preferences (`GET /api/account/preferences/`, `PATCH /api/account/preferences/`)
**PATCH Request Example:**
```json
{
  "currency": "USD",
  "date_format": "YYYY-MM-DD",
  "timezone": "America/New_York",
  "financial_year_start_month": 1,
  "default_transaction_type": "EXPENSE",
  "budget_alerts": true,
  "goal_alerts": true,
  "recurring_transaction_alerts": true,
  "system_notifications": true
}
```

### 3. Password Change (`POST /api/account/change-password/`)
**Request Payload:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewStrongPassword456!",
  "confirm_password": "NewStrongPassword456!"
}
```
**Response:**
```json
{
  "message": "Password changed successfully."
}
```

### 4. Account Overview (`GET /api/account/overview/`)
**Response:**
```json
{
  "user_info": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "date_joined": "2026-08-01T00:00:00Z",
    "is_staff": false,
    "is_active": true
  },
  "profile": { ... },
  "preferences": { ... },
  "subscription": {
    "plan_name": "Free",
    "status": "active",
    "start_date": "2026-08-01T00:00:00Z",
    "end_date": null,
    "auto_renew": true
  },
  "statistics": {
    "transaction_count": 42,
    "budget_count": 3,
    "goal_count": 2,
    "recurring_schedule_count": 4,
    "unread_notification_count": 1
  },
  "recent_activity": [ ... ]
}
}
```

---

## 📊 Financial Dashboard API (`/api/dashboard/`)

Base URL: `/api/dashboard/` (Alias: `/api/v1/dashboard/`)

All Dashboard endpoints require `Authorization: Bearer <access_token>` header.

### Endpoint Matrix

| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/dashboard/` | Full Aggregated Financial Dashboard | `start_date`, `end_date`, `limit`, `top_categories_limit` |
| `GET` | `/api/dashboard/summary/` | Summary Totals & Period Comparison | `start_date`, `end_date` |
| `GET` | `/api/dashboard/recent-transactions/` | Recent User Transactions Feed | `limit` (default: 5, max: 50) |
| `GET` | `/api/dashboard/budgets/` | Active Budget Progress & Exceeded Metrics | None |
| `GET` | `/api/dashboard/goals/` | Savings Goals Overview & Near-Completion | None |
| `GET` | `/api/dashboard/insights/` | Spending Insights & Top Categories | `start_date`, `end_date`, `limit` |
| `GET` | `/api/dashboard/alerts/` | Financial System Warnings & Alerts | None |

### Key Features
- **Query Optimization**: Leverages `select_related('category')`, database-level annotations (`Sum`, `Count`, `Avg`, `TruncMonth`), and `Coalesce` to eliminate N+1 queries.
- **Precision**: Money calculations use `Decimal` precision without floating-point inaccuracies.
- **Zero-Division Protection**: Handles new users, empty datasets, and zero previous period amounts safely.
- **Multi-Tenant Isolation**: All queries strictly scoped to `request.user`.

---

### 💾 Financial Data Backup & Data Management API (`/api/backups/`)

The Day 20 Data Backup system enables authenticated users to create, view, download, validate, and manage snapshots of their financial data in a structured, portable JSON format.

> ⚠️ **Notice**: Full destructive data restoration is intentionally not implemented on Day 20. Safe restore preparation and preview validation are provided.

| Method | Endpoint | Description | Query Parameters / Request Body |
|---|---|---|---|
| `GET` | `/api/backups/` | List User Backup History & Metadata | `status`, `backup_type`, `search`, `ordering` |
| `POST` | `/api/backups/` | Create New Data Backup | `{"name": "...", "backup_type": "FULL", "include_sections": [...], "retention_days": 30}` |
| `GET` | `/api/backups/<id>/` | Get Specific Backup Metadata & Download Link | None |
| `DELETE` | `/api/backups/<id>/` | Safely Delete Backup File & Database Record | None |
| `GET` | `/api/backups/<id>/download/` | Stream & Download Portable JSON Backup File | Attachment download |
| `POST` | `/api/backups/validate-restore/` | Preview & Validate Backup Payload (No DB Mutation) | Uploaded `file` OR `json_data` payload |
| `POST` | `/api/backups/cleanup-expired/` | Trigger Manual Retention Cleanup | None |

#### Example Request: Create Backup
```json
{
  "name": "August 2026 Financial Backup",
  "backup_type": "FULL",
  "retention_days": 30
}
```

#### Example Response: Create Backup (201 Created)
```json
{
  "id": 1,
  "name": "August 2026 Financial Backup",
  "status": "COMPLETED",
  "backup_type": "FULL",
  "file_size": 4096,
  "record_count": 52,
  "metadata": {
    "section_counts": {
      "categories": 6,
      "transactions": 38,
      "budgets": 3,
      "financial_goals": 2,
      "recurring_transactions": 3
    },
    "version": "1.0",
    "retention_days": 30
  },
  "created_at": "2026-08-29T10:00:00Z",
  "completed_at": "2026-08-29T10:00:01Z",
  "expires_at": "2026-09-28T10:00:00Z",
  "is_expired": false,
  "download_url": "http://127.0.0.1:8000/api/backups/1/download/"
}
```

#### Example Response: Restore Validation (`POST /api/backups/validate-restore/`)
```json
{
  "valid": true,
  "version": "1.0",
  "supported": true,
  "backup_type": "FULL",
  "created_at": "2026-08-29T10:00:00Z",
  "summary": {
    "categories_count": 6,
    "transactions_count": 38,
    "budgets_count": 3,
    "financial_goals_count": 2,
    "recurring_transactions_count": 3,
    "user_profile_included": true,
    "user_preferences_included": true
  },
  "validation_errors": [],
  "validation_warnings": [
    "2 new category names found in backup that will be created during restoration."
  ],
  "note": "Full destructive data restoration is intentionally not implemented on Day 20."
}
```

---

## 🔄 Recurring Transactions & Financial Scheduling API (Day 21)

The Recurring Transactions API enables automated financial transaction generation according to scheduled recurrence rules.

### Recurrence Frequencies & Intervals
- `DAILY`: Executes every $N$ days (where interval multiplier $N \ge 1$, default 1).
- `WEEKLY`: Executes every $N$ weeks (every $7N$ days).
- `MONTHLY`: Executes every $N$ months with safe month-end boundary handling (e.g. Jan 31 $\rightarrow$ Feb 28/29).
- `YEARLY`: Executes every $N$ years with leap year handling for Feb 29.
- `CUSTOM`: Executes every $N$ days according to the custom `interval` parameter.

### Endpoints Overview
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/recurring-transactions/` | List user's recurring schedules (supports filtering, search, pagination) |
| `POST` | `/api/recurring-transactions/` | Create a new recurring schedule |
| `GET` | `/api/recurring-transactions/<id>/` | Retrieve specific recurring schedule details |
| `PATCH` | `/api/recurring-transactions/<id>/` | Update recurring schedule |
| `DELETE` | `/api/recurring-transactions/<id>/` | Delete recurring schedule |
| `POST` | `/api/recurring-transactions/<id>/pause/` | Pause schedule execution |
| `POST` | `/api/recurring-transactions/<id>/resume/` | Resume schedule execution |
| `POST` | `/api/recurring-transactions/<id>/execute/` | Trigger immediate manual schedule execution |
| `GET` | `/api/recurring-transactions/<id>/history/` | List schedule execution history records |

### Processing Command
To run scheduled transaction processing automatically via cron/scheduler:
```bash
python manage.py process_recurring_transactions [--date YYYY-MM-DD]
```

---

## 📥 Financial Data Import & CSV Import API (Day 22)

The Financial Data Import API allows authenticated users to import transaction data from CSV files into their finance tracker with structural validation, category matching, duplicate transaction detection, and preview execution controls.

### Endpoints Overview

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/imports/preview/` | Yes (`Bearer`) | Upload CSV file & receive import validation preview without creating transactions |
| `POST` | `/api/imports/<id>/execute/` | Yes (`Bearer`) | Execute transaction creation for previewed CSV import |
| `GET` | `/api/imports/` | Yes (`Bearer`) | List user import history with filtering, ordering & pagination |
| `GET` | `/api/imports/<id>/` | Yes (`Bearer`) | Get details and error summary for a specific import |
| `DELETE` | `/api/imports/<id>/` | Yes (`Bearer`) | Delete an import history record and associated CSV file |

### Supported CSV Headers & Aliases
- `title` / `description` / `name` / `details`
- `amount` / `value` / `sum`
- `transaction_type` / `type` / `type_name` (`INCOME`, `EXPENSE`)
- `category` / `category_name` / `cat`
- `date` / `txn_date` (`YYYY-MM-DD`)

### Example CSV Structure
```csv
title,description,amount,transaction_type,category,date
Salary,Monthly salary,150000,INCOME,Salary,2026-09-01
Food,Lunch expense,1500,EXPENSE,Food,2026-09-01
```

#### Example Response: Import Preview (`POST /api/imports/preview/`)
```json
{
  "id": 1,
  "file_name": "september_transactions.csv",
  "status": "PREVIEW_READY",
  "total_rows": 50,
  "valid_rows": 45,
  "invalid_rows": 3,
  "duplicate_rows": 2,
  "unmatched_categories": ["Crypto Investment"],
  "errors": [
    {
      "row": 12,
      "field": "amount",
      "message": "Amount must be greater than zero."
    }
  ],
  "preview_rows": [
    {
      "row": 2,
      "title": "Salary",
      "description": "Salary - Monthly salary",
      "amount": "150000.00",
      "transaction_type": "INCOME",
      "category": "Salary",
      "date": "2026-09-01",
      "is_valid": true,
      "is_duplicate": false,
      "errors": []
    }
  ]
}
```

#### Example Response: Import Execution (`POST /api/imports/1/execute/`)
```json
{
  "id": 1,
  "file_name": "september_transactions.csv",
  "status": "COMPLETED",
  "total_rows": 50,
  "successful_rows": 45,
  "failed_rows": 3,
  "skipped_rows": 2,
  "duplicate_rows": 2,
  "created_at": "2026-09-01T14:00:00Z",
  "completed_at": "2026-09-01T14:00:02Z",
  "error_summary": [
    {
      "row": 12,
      "field": "amount",
      "message": "Amount must be greater than zero."
    }
  ]
}
```

---

## 📤 Day 23 — Financial Data Export API (`/api/exports/`)

The Financial Data Export API enables authenticated users to export user-owned financial data (Transactions, Categories, Budgets, Goals, Recurring Transactions, or Full Financial Data) in clean, portable CSV and JSON formats.

### Difference Between Data Backup vs. Data Export

| Feature | Data Backup (Day 20) | Financial Data Export (Day 23) |
|---|---|---|
| **Purpose** | Disaster recovery, full state preservation & system restore | User download, external analysis, reporting, spreadsheet viewing |
| **Supported Formats** | Proprietary JSON Backup Schema v1.0 | CSV, JSON |
| **Scope** | Complete account data snapshot including settings | Scoped datasets or full financial data with custom filtering |
| **Filters** | None (Full/Transactions/Selected) | Date range (`start_date`, `end_date`), category, transaction type |
| **Download Use-case** | Importing back into system via Restore API | Opening in Excel, Google Sheets, or 3rd-party analytics tools |

### Export Endpoints Summary

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/exports/` | Yes (`Bearer`) | List export history and statuses for authenticated user |
| `POST` | `/api/exports/` | Yes (`Bearer`) | Create and process a new data export operation |
| `GET` | `/api/exports/{id}/` | Yes (`Bearer`) | Retrieve export status, metadata, record count, and download link |
| `DELETE` | `/api/exports/{id}/` | Yes (`Bearer`) | Delete export record and purge backing file from storage |
| `GET` | `/api/exports/{id}/download/` | Yes (`Bearer`) | Securely download the generated export file (CSV or JSON) |
| `POST` | `/api/exports/cleanup-expired/` | Yes (`Bearer`) | Trigger maintenance cleanup of expired export files |

### Supported Export Types & Formats

- **Export Types**: `TRANSACTIONS`, `CATEGORIES`, `BUDGETS`, `GOALS`, `RECURRING_TRANSACTIONS`, `FULL_FINANCIAL_DATA`
- **Formats**: `CSV`, `JSON`

### Filtering Options

- `start_date`: `YYYY-MM-DD` (filters transactions/records on or after start date)
- `end_date`: `YYYY-MM-DD` (filters transactions/records on or before end date; validated `start_date <= end_date`)
- `category`: Category ID integer
- `transaction_type`: `INCOME` or `EXPENSE`

### 1. Request Data Export (`POST /api/exports/`)

```json
{
  "name": "Q3 Transactions Export",
  "export_type": "TRANSACTIONS",
  "format": "CSV",
  "start_date": "2026-07-01",
  "end_date": "2026-09-30",
  "category": 4,
  "transaction_type": "EXPENSE"
}
```

#### Response (`201 Created`):
```json
{
  "id": 1,
  "name": "Q3 Transactions Export",
  "export_type": "TRANSACTIONS",
  "format": "CSV",
  "status": "COMPLETED",
  "file_name": "q3_transactions_export_1.csv",
  "file_size": 4208,
  "record_count": 45,
  "filters": {
    "start_date": "2026-07-01",
    "end_date": "2026-09-30",
    "category": 4,
    "transaction_type": "EXPENSE"
  },
  "created_at": "2026-09-02T19:58:05Z",
  "completed_at": "2026-09-02T19:58:06Z",
  "expires_at": "2026-09-09T19:58:05Z",
  "is_expired": false,
  "download_url": "http://127.0.0.1:8000/api/exports/1/download/"
}
```

### 2. Download Export File (`GET /api/exports/{id}/download/`)

Returns direct binary file attachment with content disposition:
- CSV: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="q3_transactions_export_1.csv"`
- JSON: `Content-Type: application/json`, `Content-Disposition: attachment; filename="full_financial_export_2.json"`

### Retention Management Command

Purge expired files (past `expires_at` timestamp) using CLI:
```bash
python manage.py cleanup_expired_exports
```

---

## 📊 Financial Analytics & Dashboard API (Day 24)

Base URL: `/api/analytics/`

All Financial Analytics endpoints require `Authorization: Bearer <access_token>` header and strictly isolate data to the authenticated user.

### Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary/` | Overall dashboard summary (income, expenses, net balance, savings rate) |
| `GET` | `/api/analytics/income-expenses/` | Income and expense totals for date range & filters |
| `GET` | `/api/analytics/categories/` | Spending breakdown by expense category |
| `GET` | `/api/analytics/income-categories/` | Income breakdown by income category |
| `GET` | `/api/analytics/daily/` | Daily financial trends (`TruncDay`) |
| `GET` | `/api/analytics/monthly/` | Monthly financial trends (`TruncMonth`) |
| `GET` | `/api/analytics/budget-performance/` | Budget utilization and exceed status |
| `GET` | `/api/analytics/top-categories/` | Top spending categories (with `limit`) |
| `GET` | `/api/analytics/recent-transactions/` | Recent transactions overview (with `limit`) |

### Common Analytics Query Parameters

| Parameter | Type | Description | Example |
|---|---|---|---|
| `start_date` | Date (`YYYY-MM-DD`) | Filter transactions starting from date | `2026-09-01` |
| `end_date` | Date (`YYYY-MM-DD`) | Filter transactions ending at date | `2026-09-30` |
| `category` | String/Integer | Filter by Category ID or Category Name | `Groceries` or `3` |
| `transaction_type` | String | `INCOME` or `EXPENSE` | `EXPENSE` |
| `limit` | Integer | Limit number of results (1–100) | `5` |

---

## 💻 Local Developer Setup


1. **Clone repository**:
   ```bash
   git clone <repository_url>
   cd git_plan
   ```
2. **Create & activate virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment variables configuration (`.env`)**:
   ```env
   DEBUG=True
   SECRET_KEY=your_secret_key_here
   ALLOWED_HOSTS=127.0.0.1,localhost
   DB_NAME=finance_tracker_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=127.0.0.1
   DB_PORT=5432
   ```
5. **Run Database Migrations**:
   ```bash
   python manage.py migrate
   ```
6. **Start Development Server**:
   ```bash
   python manage.py runserver 8000
   ```
7. **Access Documentation**:
   - Swagger UI: `http://127.0.0.1:8000/api/docs/`
   - ReDoc: `http://127.0.0.1:8000/api/redoc/`
