# le_shop

A strict, modern e-commerce monorepo built on **Django 6.0 standards** and **Tailwind CSS v4**.

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Command Reference](#command-reference)
5. [Project Structure](#project-structure)
6. [Coding Standards](#coding-standards)

---

## Tech Stack

| Domain | Technology | Version |
| :--- | :--- | :--- |
| **Backend** | Django + DRF | Latest Stable |
| **Frontend** | Tailwind CSS + Bun | v4.0+ (CSS-First) |
| **Security** | CSP + SimpleJWT | Strict Mode |
| **Quality** | Ruff + MyPy | Strict Typing |
| **Database** | SQLite (Dev) / Postgres (Prod) | Atomic Transactions |

[Back to Top ↑](#table-of-contents)

---

## Architecture

This project follows a **Modified Monorepo** structure to keep concerns separated while maintaining developer velocity.

- **Root:** Configuration (`manage.py`, `package.json`, `.vscode`).
- **`backend/`**: Pure Python application logic.
- **`frontend/`**: Asset factory (Tailwind source).

> **Note:** `manage.py` is located in the **ROOT**, but points to `backend.core.settings`.

[Back to Top ↑](#table-of-contents)

---

## Quick Start

### Prerequisites

- Python 3.12+
- Bun (Latest)

### Installation

```powershell
# 1. Create & Activate Virtual Env
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install Python Dependencies (Editable Mode)
pip install -e .[dev]

# 3. Install Frontend Assets
bun install

# 4. Initialize Database
python manage.py makemigrations
python manage.py migrate
```

### Development Server

This project uses a unified runner to handle Django and Tailwind simultaneously.

```powershell
.\run.ps1
```

*Runs Django at `127.0.0.1:8000` and Tailwind Watcher in parallel.*

[Back to Top ↑](#table-of-contents)

---

## Command Reference

| Action | Command | Description |
| :--- | :--- | :--- |
| **Run Dev** | `.\run.ps1` | Starts Backend + Frontend Watcher. |
| **Lint** | `ruff check .` | Auto-fixes imports and style. |
| **Type Check** | `mypy .` | Enforces strict type hints. |
| **Build CSS** | `bun run build` | Compiles Tailwind for production. |
| **Django CLI** | `python manage.py <cmd>` | Standard Django commands. |

[Back to Top ↑](#table-of-contents)

---

## Project Structure

```text
le_shop/
├── .vscode/               # Editor Enforcement (Ruff/MyPy)
├── backend/
│   ├── apps/              # Business Logic
│   ├── core/              # Settings & WSGI/ASGI
│   ├── static/            # Compiled Assets (Do not edit)
│   └── templates/         # HTML (HTMX/Alpine)
├── frontend/
│   └── src/               # Tailwind CSS Source
├── manage.py              # Entry Point
├── package.json           # Asset Config
└── pyproject.toml         # Python Dependencies
```

[Back to Top ↑](#table-of-contents)

---

## Coding Standards

1. **Strict Typing:** All functions must have type hints. MyPy is configured to fail on untyped definitions.
2. **Modern Classical Django:** Business logic resides in **Class-Based Views (CBVs)**. We keep it standard but modernized with HTMX and strict atomic transactions.
3. **CSS-First:** Do not use `tailwind.config.js`. Use CSS variables in `frontend/src/app.css`.
4. **Atomic Writes:** All DB writes must use `transaction.atomic()`.

[Back to Top ↑](#table-of-contents)
