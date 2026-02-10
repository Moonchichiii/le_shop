# le_shop

A modern, passwordless e-commerce application built on **Django 6.0**,
**HTMX**, and **Tailwind CSS v4**.

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Command Reference](#command-reference)
6. [Conventions](#conventions)
7. [Testing](#testing)

---

## Tech Stack

| Domain          | Technology                          |
| :-------------- | :---------------------------------- |
| **Runtime**     | Python 3.13 · Django 6.0 · DRF     |
| **Auth**        | django-allauth — passwordless MFA   |
| **Frontend**    | Tailwind CSS v4 (CSS-first) · HTMX · GSAP |
| **Payments**    | PayPal                              |
| **Media**       | Cloudinary                          |
| **Admin**       | django-unfold                       |
| **Database**    | SQLite (dev) · PostgreSQL (prod)    |
| **Security**    | django-csp · WhiteNoise             |
| **Quality**     | Ruff · mypy · pytest · Playwright   |
| **Bundler**     | Bun                                 |

[↑ Top](#table-of-contents)

---

## Architecture

This project uses a **service + selector** architecture on top of Django's
standard app layout.

### Layer Responsibilities

| Layer              | File              | Rules |
| :----------------- | :---------------- | :---- |
| **Models**         | `models.py`       | Data and field definitions only. Minimal helpers (`__str__`, `get_absolute_url`). |
| **Selectors**      | `selectors.py`    | Read-only query composition. No side effects. |
| **Services**       | `services.py`     | Transactional write workflows. All DB writes use `transaction.atomic()`. |
| **Views**          | `views.py`        | HTTP orchestration — calls services/selectors, picks templates, sets messages. |
| **Context Processors** | `context_processors.py` | Injects global template context (e.g. cart count). |
| **Constants**      | `constants.py`    | Choices, magic numbers, config values. |

### Class Diagram

```mermaid
classDiagram
    direction LR

    class Category {
        +id: int
        +name: str
        +slug: str
        +description: text
    }

    class Product {
        +id: int
        +category_id: int
        +name: str
        +slug: str
        +image: CloudinaryField
        +image_alt: str
        +description: text
        +price: Decimal
        +stock: int
        +is_active: bool
        +is_featured: bool
        +is_new: bool
        +created_at: datetime
        +updated_at: datetime
        +get_absolute_url()
        +is_in_stock
        +image_url(width?, height?)
    }

    Category "1" --> "*" Product : contains

    class Cart {
        +SESSION_KEY: str
        +cart: dict
        +add(product, quantity, override) AddResult
        +remove(product)
        +clear()
        +__iter__()
        +__len__()
        +get_total_price()
    }

    class AddResult {
        +requested: int
        +final: int
        +max_stock: int
        +clamped: bool
        +removed: bool
    }

    Cart --> AddResult : returns

    class Order {
        +id: int
        +user_id: int?
        +email: str?
        +status: Status
        +currency: str
        +subtotal: Decimal
        +paypal_order_id: str
        +paypal_capture_id: str
        +created_at: datetime
        +updated_at: datetime
    }

    class OrderItem {
        +id: int
        +order_id: int
        +product_id: int
        +qty: int
        +unit_price: Decimal
        +line_total: Decimal
    }

    Order "1" --> "*" OrderItem : has
    Product "1" --> "*" OrderItem : referenced

    class OrderTracking {
        +id: int
        +order_id: int
        +status: FulfillmentStatus
        +carrier: str
        +tracking_number: str
        +delivery_notes: text
        +set_milestone_timestamp()
    }

    class OrderTrackingEvent {
        +id: int
        +tracking_id: int
        +from_status: str
        +to_status: str
        +actor_id: int?
        +note: text
        +created_at: datetime
    }

    Order "1" --> "0..1" OrderTracking : tracking
    OrderTracking "1" --> "*" OrderTrackingEvent : audit log
```

### Checkout Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant V as Views
    participant C as Cart (Service)
    participant S as Orders (Service)
    participant P as PayPal
    participant DB as Database

    U->>V: POST /cart/add/‹id› (qty)
    V->>C: Cart.add(product, qty)
    C->>DB: read Product.stock
    C-->>V: AddResult
    V-->>U: redirect cart_detail + message

    U->>V: POST /orders/checkout (email)
    V->>S: reserve_stock_and_create_pending_order(cart)
    S->>DB: SELECT FOR UPDATE Products
    S->>DB: decrement stock · create Order + OrderItems
    S-->>V: Order (PENDING)
    V->>P: create order (redirect URL)
    V-->>U: redirect to PayPal approval

    U->>V: GET /orders/paypal/return?token=…
    V->>P: capture order
    V->>DB: mark Order PAID · create tracking
    V->>C: Cart.clear()
    V-->>U: redirect order confirmation
```

[↑ Top](#table-of-contents)

---

## Project Structure

```text
le_shop/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # User settings, email change, danger zone
│   │   ├── cart/           # Session cart, add/remove/clear
│   │   ├── core/           # Site-wide models, allauth form overrides
│   │   ├── orders/         # Checkout, PayPal, tracking, fulfilment
│   │   └── products/       # Catalogue, categories, selectors
│   ├── config/             # settings, urls, asgi, wsgi
│   ├── static/             # Compiled assets (CSS, JS, fonts)
│   ├── templates/          # Shared: base, partials, allauth overrides
│   │   ├── account/        # Allauth template overrides
│   │   ├── pages/          # Standalone pages (home, about)
│   │   └── partials/       # Reusable fragments (_navbar, _footer, …)
│   └── tests/
│       └── e2e/            # Playwright end-to-end tests
├── frontend/
│   └── src/app.css         # Tailwind source (CSS-first config)
├── manage.py
├── package.json
├── pyproject.toml
├── pytest.ini
└── run.ps1
```

> **Note:** `manage.py` lives at the root but points to
> `backend.config.settings`.

[↑ Top](#table-of-contents)

---

## Quick Start

### Prerequisites

- Python 3.12+
- Bun (latest)

### Installation

```powershell
# 1. Create & activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install Python dependencies (editable)
pip install -e ".[dev]"

# 3. Install frontend dependencies
bun install

# 4. Set up environment
copy .env.example .env   # then fill in values

# 5. Initialise database
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser
```

### Development Server

```powershell
.\run.ps1
```

Starts Django at `127.0.0.1:8000` and the Tailwind watcher in parallel.

[↑ Top](#table-of-contents)

---

## Command Reference

| Action            | Command                                  |
| :---------------- | :--------------------------------------- |
| **Dev server**    | `.\run.ps1`                              |
| **Unit tests**    | `pytest -x --ignore=backend/tests/e2e`   |
| **E2E tests**     | `pytest backend/tests/e2e -x --headed`   |
| **Lint**          | `ruff check .`                           |
| **Format**        | `ruff format .`                          |
| **Type check**    | `mypy .`                                 |
| **Build CSS**     | `bun run build`                          |
| **Migrations**    | `python manage.py makemigrations && python manage.py migrate` |

[↑ Top](#table-of-contents)

---

## Conventions

### Files & Naming

| Target           | Convention             | Example                          |
| :--------------- | :--------------------- | :------------------------------- |
| Python files     | `snake_case.py`        | `tracking_service.py`            |
| JS / CSS files   | `kebab-case`           | `hero-carousel.js`               |
| Classes          | `PascalCase`           | `OrderTracking`                  |
| Functions        | `snake_case`           | `get_active_products()`          |
| Constants        | `UPPER_SNAKE_CASE`     | `SESSION_KEY`                    |
| URL names        | `app:action-noun`      | `orders:order-track`             |
| Test files       | `test_<module>.py`     | `test_services.py`               |

### Templates

| Type                        | Location                                   | Naming                     |
| :-------------------------- | :----------------------------------------- | :------------------------- |
| App page                    | `apps/<app>/templates/<app>/`              | `noun_action.html`         |
| HTMX fragment               | `apps/<app>/templates/<app>/`              | `_noun_fragment.html`      |
| Shared partial               | `templates/partials/`                      | `_noun.html`               |
| Standalone page              | `templates/pages/`                         | `noun.html`                |
| Allauth override             | `templates/account/`                       | (match allauth names)      |

> Partials and fragments are always prefixed with `_` to signal they are
> never rendered standalone.

### URL Namespacing

Always use namespaced URLs in templates and `reverse()` calls:

```django
{% url 'products:product-detail' slug=product.slug %}
{% url 'orders:order-list' %}
{% url 'cart:cart-detail' %}
```

### Database Writes

All write operations must use `transaction.atomic()` and live in
`services.py`, never in views.

[↑ Top](#table-of-contents)

---

## Testing

### Unit Tests (pytest + factory_boy)

```powershell
pytest -x --ignore=backend/tests/e2e
```

Each app has a `tests/` package with:

- `test_models.py` — model logic and constraints
- `test_services.py` — business logic (mocked DB where possible)
- `test_views.py` — request/response, status codes, redirects
- `conftest.py` / `factories.py` — shared fixtures and factories

### End-to-End Tests (Playwright)

```powershell
pytest backend/tests/e2e -x --headed
```

E2E tests cover full user journeys: auth flow, browse → cart → checkout,
UI/accessibility.

[↑ Top](#table-of-contents)