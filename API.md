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
