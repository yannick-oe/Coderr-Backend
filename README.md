# Coderr Backend

Backend for **Coderr**, a freelancer marketplace where business users
publish offers and customer users order them and write reviews. This
repository contains the backend only; the frontend is a separate,
delivered static application served on `http://127.0.0.1:5500`.

- **Stack:** Python, Django, Django REST Framework, Django ORM, SQLite.
- **Auth:** DRF `TokenAuthentication`. Login uses `username` + `password`
  (never email). No JWT.
- **API base URL:** `http://127.0.0.1:8000/api/`

---

## Prerequisites

- **Python 3.12**
- `pip` and the ability to create a virtual environment
- Git

---

## Setup from a fresh clone

```bash
# 1. Clone the repository
git clone <repository-url>
cd Coderr-Backend

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the environment file
cp .env.example .env
# Then generate a real secret key and paste it into .env:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 5. Apply database migrations
python manage.py migrate

# 6. Create an administrator account
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver           # http://127.0.0.1:8000
```

---

## Environment variables

Configuration is loaded from a local `.env` file via `python-dotenv`.
See `.env.example` for the required keys. Secrets are never committed.

| Variable        | Description                              | Example               |
| --------------- | ---------------------------------------- | --------------------- |
| `SECRET_KEY`    | Django secret key (required, no default) | *(generated value)*   |
| `DEBUG`         | Debug mode, `True` or `False`            | `True`                |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts    | `127.0.0.1,localhost` |

The application refuses to start if `SECRET_KEY` is missing — there is no
hardcoded fallback.

---

## Authentication

All authenticated requests carry a DRF token in the `Authorization`
header:

```
Authorization: Token <token>
```

Tokens are issued on login and registration. Login is performed with
`username` and `password`; email is never used as a credential.

---

## API overview

Base URL: `http://127.0.0.1:8000/api/`

> **TODO:** endpoint overview. Endpoints are documented in
> `docs/Coderr Endpoint Dokumentation.pdf` and will be summarized here as
> they are implemented.

---

## Known specifics

- **Pagination is applied per view, never globally.** The project does
  **not** set `DEFAULT_PAGINATION_CLASS` in `REST_FRAMEWORK`. Only the
  offer list (`offers/`) is paginated (`page_size = 6`); the
  `profiles/business/`, `profiles/customer/`, `reviews/` and `orders/`
  endpoints return bare arrays. Setting pagination globally would break
  those endpoints in the frontend.
- **Filtering is configured per view**, not through a global
  `DEFAULT_FILTER_BACKENDS`.
- **Media files** are served by Django only while `DEBUG` is `True`, via
  `MEDIA_URL` and `MEDIA_ROOT`, because the frontend prefixes relative
  media paths with `http://127.0.0.1:8000/`.
- **CORS** is restricted to the frontend dev origins
  `http://127.0.0.1:5500` and `http://localhost:5500`.

---

## Development commands

```bash
source .venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
ruff format . && ruff check .
python manage.py test
```
