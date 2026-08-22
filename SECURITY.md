# Security Policy & Production Hardening Guide

This document outlines the security architecture, authentication policies, permission models, rate limits, audit logging mechanisms, and production deployment checklists for the **SaaS Personal Finance Tracker** backend.

---

## 🔒 Security Architecture Overview

The backend employs defense-in-depth security mechanisms designed to protect sensitive financial data:

1. **Authentication**: Stateless JSON Web Tokens (JWT) powered by `django-rest-framework-simplejwt` with refresh token rotation and token blacklisting.
2. **Authorization & Data Isolation**: Every resource (Transactions, Categories, Budgets, Goals, Schedules, Notifications, Audit Logs) is strictly isolated to the authenticated user owning it. Insecure Direct Object References (IDOR) return `404 Not Found`.
3. **Throttling & Abuse Protection**: DRF Rate Limiting protects authentication, analytics, and import/export endpoints against brute-force and Denial-of-Service (DoS) attacks.
4. **Audit Trail**: Every data mutation (Create, Update, Delete, Import, Export) and authentication event (Login, Logout, Password Change) is logged into an immutable user audit history.
5. **Sensitive Data Protection**: Passwords, secret keys, tokens, and DB credentials are automatically sanitized from error outputs, exception tracebacks, and audit metadata.

---

## 🔐 Authentication Hardening

### Token Lifetime & Rotation Settings
- **Access Tokens**: Short-lived (60 minutes default, configurable via `JWT_ACCESS_MINUTES`).
- **Refresh Tokens**: 1-day default lifetime (`JWT_REFRESH_DAYS`), rotated upon use (`ROTATE_REFRESH_TOKENS = True`).
- **Token Blacklisting**: Old refresh tokens are blacklisted immediately upon rotation or logout (`BLACKLIST_AFTER_ROTATION = True`).
- **Header**: Standard `Authorization: Bearer <access_token>`.

---

## 🛡️ Permission Model & IDOR Protection

All endpoints enforce `rest_framework.permissions.IsAuthenticated` and `IsOwner` object-level permissions.

### User Data Isolation Rules
- Views filter querysets by `request.user` (`Model.objects.filter(user=request.user)`).
- Attempts by User B to access `/api/budgets/123/` owned by User A return `404 Not Found`, shielding resource existence from unauthorized callers.
- Category creation enforces unique case-insensitive category names per user.

---

## 🚦 API Throttling & Rate Limiting

DRF throttling rates are centrally configured in `finance_tracker/settings.py` and enforced via `finance_tracker/throttling.py`:

| Scope | Rate Limit | Target Endpoints | Description |
| :--- | :--- | :--- | :--- |
| `anon` | `30/minute` | Unauthenticated requests | General rate limiting for unauthenticated visitors |
| `user` | `100/minute` | Standard API endpoints | General API usage limit per authenticated user |
| `auth` | `10/minute` | `/api/auth/*` | Login, Registration, Token Refresh, Logout |
| `analytics` | `20/minute` | `/api/analytics/*`, `/api/reports/*` | Computationally heavy analytics and reports |
| `import_export` | `10/minute` | `/api/import/*`, `/api/export/*` | Bulk CSV import and data export operations |

---

## 📝 Audit Logging Architecture

The `AuditLog` model tracks user operations and security events.

### Model Schema
```text
AuditLog
├── user (ForeignKey -> User, SET_NULL)
├── action (CREATE, UPDATE, DELETE, IMPORT, EXPORT, LOGIN, LOGOUT, PASSWORD_CHANGE)
├── resource_type (Transaction, Budget, Goal, Category, RecurringTransaction, Notification, User)
├── resource_id (CharField)
├── ip_address (GenericIPAddressField)
├── metadata (JSONField - sanitized)
└── timestamp (DateTimeField - auto_now_add, db_index=True)
```

### Audit Log API
- `GET /api/audit-logs/`: List authenticated user's audit history (supports filtering by `action`, `resource_type`, `start_date`, `end_date`, search, and ordering).
- `GET /api/audit-logs/<id>/`: Retrieve specific audit log entry owned by user.

---

## 🔒 Request & Import Security

1. **File Upload Size**: Maximum file size for CSV imports is restricted to **5MB**.
2. **File Extensions**: Only `.csv` files are accepted.
3. **Batch Size Limit**: Maximum **1,000 rows** per CSV import batch.
4. **Encoding**: Requires UTF-8 encoded CSV payloads.
5. **Duplicate Protection**: Row fingerprint hashing prevents importing duplicate transactions.

---

## ⚙️ Production Deployment Security Checklist

Before deploying to production, verify the following configuration settings:

- [ ] Set `DEBUG=False` in environment variables.
- [ ] Set a strong, random `SECRET_KEY`.
- [ ] Configure `ALLOWED_HOSTS` with domain names.
- [ ] Set `SECURE_SSL_REDIRECT=True` to enforce HTTPS.
- [ ] Set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`.
- [ ] Enable HSTS via `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`, and `SECURE_HSTS_PRELOAD=True`.
- [ ] Verify deployment security checks pass:
  ```bash
  python manage.py check --deploy
  ```

---

## 📢 Responsible Vulnerability Reporting

If you discover a potential security vulnerability in this project, please send an email to `security@financetracker.local` with detailed steps to reproduce. Please do not publish vulnerabilities publicly before fix deployment.
