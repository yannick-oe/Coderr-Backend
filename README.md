# Coderr Backend

Backend for **Coderr**, a freelancer marketplace where business users
publish offers and customer users order them and write reviews. Business
users create tiered offers (basic / standard / premium); customers place
orders from an offer's detail tiers and leave one review per business.
This repository contains the backend only; the frontend is a separate,
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

# 4. Create the environment file from the template
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

The database (`db.sqlite3`) is **not** in the repository, so a fresh
clone starts with an empty database. Create data via the API (see
**Demo accounts** below) or the Django admin.

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
header, using the literal word `Token` and a single space:

```
Authorization: Token 83bf098723b08f7b23429u0fv8274
```

Tokens are issued on login and registration, which both return
`token`, `username`, `email` and `user_id`. Login is performed with
`username` and `password`; email is never used as a credential.

---

## API overview

Base URL: `http://127.0.0.1:8000/api/`

| Method | Path | Who may call it |
| --- | --- | --- |
| POST | `/api/registration/` | Anyone |
| POST | `/api/login/` | Anyone |
| GET | `/api/profile/{pk}/` | Any authenticated user |
| PATCH | `/api/profile/{pk}/` | The profile's owner |
| GET | `/api/profiles/business/` | Any authenticated user |
| GET | `/api/profiles/customer/` | Any authenticated user |
| GET | `/api/offers/` | Anyone (public, paginated) |
| POST | `/api/offers/` | Authenticated business users |
| GET | `/api/offers/{id}/` | Any authenticated user |
| PATCH | `/api/offers/{id}/` | The offer's owner |
| DELETE | `/api/offers/{id}/` | The offer's owner |
| GET | `/api/offerdetails/{id}/` | Any authenticated user |
| GET | `/api/orders/` | Any authenticated user (own orders) |
| POST | `/api/orders/` | Authenticated customer users |
| PATCH | `/api/orders/{id}/` | The order's assigned business user |
| DELETE | `/api/orders/{id}/` | Staff (admin) users |
| GET | `/api/order-count/{business_user_id}/` | Any authenticated user |
| GET | `/api/completed-order-count/{business_user_id}/` | Any authenticated user |
| GET | `/api/reviews/` | Any authenticated user |
| POST | `/api/reviews/` | Authenticated customer users |
| PATCH | `/api/reviews/{id}/` | The review's author |
| DELETE | `/api/reviews/{id}/` | The review's author |
| GET | `/api/base-info/` | Anyone (public) |

---

## Known specifics

- **Pagination is applied only to the offer list, with page size 6.**
  `GET /api/offers/` returns `{count, next, previous, results}`; every
  other list endpoint (`profiles/business/`, `profiles/customer/`,
  `orders/`, `reviews/`) returns a **bare array**. The project does
  **not** set `DEFAULT_PAGINATION_CLASS` in `REST_FRAMEWORK`; doing so
  would wrap those bare-array responses and break the frontend, which
  assigns them directly to arrays.
- **Profile text fields serialize as empty strings, never `null`.**
  `first_name`, `last_name`, `location`, `tel`, `description` and
  `working_hours` are always strings; the frontend renders them directly.
- **Orders store a snapshot of the offer detail.** At creation an order
  copies the title, revisions, delivery time, price, features and offer
  type; it holds no foreign key to the offer detail, so later edits or
  deletion of the source offer leave existing orders unchanged.
- **The database is not in the repository.** A fresh clone starts with an
  empty database; there are no fixtures.
- **Filtering is configured per view**, not through a global
  `DEFAULT_FILTER_BACKENDS`.
- **Media files** are served by Django only while `DEBUG` is `True`, via
  `MEDIA_URL` and `MEDIA_ROOT`, because the frontend prefixes relative
  media paths with `http://127.0.0.1:8000/`.
- **CORS** is restricted to the frontend dev origins
  `http://127.0.0.1:5500` and `http://localhost:5500`.
- **Four views declare permissions through `get_permissions()`** rather
  than a `permission_classes` attribute — `OfferListCreateView`,
  `OrderListCreateView`, `OrderStatusUpdateDeleteView` and
  `ReviewListCreateView`. On those paths the HTTP methods (e.g. GET vs
  POST) require different permissions, which a single `permission_classes`
  list cannot express. Every method returns an explicit permission list;
  no view inherits the global default silently.
- **The offer list drives one extra request per offer detail, by
  design.** The delivered frontend fetches each detail separately, so a
  page of six offers produces eighteen additional requests to
  `/api/offerdetails/{id}/`. This is client behaviour and is not fixed in
  the backend; each `offerdetails/{id}/` call is kept to a single query.

---

## Demo accounts

The delivered frontend hardcodes two guest logins in its `config.js`:

| Type | Username | Password |
| --- | --- | --- |
| customer | `andrey` | `asdasd` |
| business | `kevin` | `asdasd24` |

These accounts **do not exist** in a fresh database — the frontend only
sends their credentials to `POST /api/login/`; it never creates them.
Recreate them once against a running server with two registration calls
(any email works):

```bash
curl -X POST http://127.0.0.1:8000/api/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username": "andrey", "email": "andrey@example.com", "password": "asdasd", "repeated_password": "asdasd", "type": "customer"}'

curl -X POST http://127.0.0.1:8000/api/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username": "kevin", "email": "kevin@example.com", "password": "asdasd24", "repeated_password": "asdasd24", "type": "business"}'
```

The `kevin` business account should own at least one offer (create one
with `POST /api/offers/` while logged in as `kevin`), otherwise the page
looks empty after a business guest login.

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
coverage run manage.py test && coverage report -m
```
