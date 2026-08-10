# Personal Finance Tracker SaaS - Backend

A scalable, secure Personal Finance Tracker SaaS backend application built with **Django REST Framework (DRF)** and **PostgreSQL**.

---

## 🛠️ Tech Stack

- **Backend Framework**: Django 5.x / Django REST Framework
- **Database Engine**: PostgreSQL 18
- **Language**: Python 3.10+
- **Environment Management**: `python-dotenv`
- **Testing Framework**: `pytest`, `pytest-django`
- **Version Control**: Git

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
Example `.env`:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=finance_tracker_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 7. Run Database Migrations
```bash
python manage.py migrate
```

### 8. Verify Project & Run Development Server
```bash
python manage.py check
python manage.py runserver
```
The Django development server will start at `http://127.0.0.1:8000/`.

---

## 📂 Project Structure

```text
FinTrack/
├── .env.example               # Example environment variable file
├── .gitignore                  # Git ignore rules for Python/Django/PostgreSQL
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── finance_tracker/            # Main Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py            # Project settings & PostgreSQL config
│   ├── urls.py                # Main URL configuration
│   └── wsgi.py
└── users/                      # User management application module
    ├── __init__.py
    ├── admin.py                # CustomUserAdmin configuration
    ├── apps.py                 # App configuration
    ├── models.py               # Custom User model (AbstractUser)
    ├── tests.py                # Unit test suite
    ├── urls.py                 # Users module routes
    └── views.py                # Users module views
```

---

## 📄 License
MIT License
