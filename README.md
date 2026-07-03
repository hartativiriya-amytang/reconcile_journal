# Recon System

## Overview

`recon_system` is a Django-based reconciliation system built to compare two Excel datasets and highlight matched versus unmatched records. It features a **full REST API** (built with Django REST Framework) and a **Jazzmin-powered ERP-style admin interface** with a dark theme.

## Features

- **REST API** — Full CRUD for all models via DRF ViewSets with filtering, search, and pagination.
- **ERP Admin Interface** — Jazzmin-themed Django admin (dark theme) with custom dashboard, stat cards, icons, and quick actions.
- **Custom Web UI** — Step-by-step reconciliation wizard that embeds within the Jazzmin admin layout (configure fields → upload files → view results).
- **API Documentation** — Auto-generated Swagger UI at `/api/docs/`.
- **Bulk Configuration** — Create configs, fields, mappings, and rules in one API call.
- **File Reconciliation** — Upload two Excel files and run matching via API or admin.
- **Export** — Download matched, unmatched, and summary reports as Excel files.
- **Admin Dashboard** — Custom Jazzmin admin home with stat counters, recent sessions table, and quick action links.
- **Error Handling** — Failed reconciliation sessions capture and display error messages.


## Requirements

- Python 3.10+
- Django >=4.2
- djangorestframework >=3.15
- django-jazzmin >=3.0
- django-cors-headers >=4.0
- django-filter >=23.0
- drf-spectacular >=0.27
- pandas >=2.0
- openpyxl >=3.1

## Project Structure
```
recon_system
├─ db.sqlite3
├─ docs
│  ├─ usage.md
│  └─ user_roles.md
├─ manage.py
├─ README.md
├─ reconcile
│  ├─ admin.py
│  ├─ api_urls.py
│  ├─ api_views.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_fieldmapping_reconciliationrule_and_more.py
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  │     ├─ 0001_initial.cpython-310.pyc
│  │     ├─ 0002_fieldmapping_reconciliationrule_and_more.cpython-310.pyc
│  │     └─ __init__.cpython-310.pyc
│  ├─ models.py
│  ├─ serializers.py
│  ├─ services
│  │  ├─ excel_parser.py
│  │  ├─ export_excel.py
│  │  ├─ reconciliation.py
│  │  ├─ rule_engine.py
│  │  └─ __pycache__
│  │     ├─ excel_parser.cpython-310.pyc
│  │     ├─ export_excel.cpython-310.pyc
│  │     ├─ reconciliation.cpython-310.pyc
│  │     └─ rule_engine.cpython-310.pyc
│  ├─ tests.py
│  ├─ utils
│  │  └─ dataframe.py
│  ├─ __init__.py
│  └─ __pycache__
│     ├─ admin.cpython-310.pyc
│     ├─ admin.cpython-314.pyc
│     ├─ api_urls.cpython-310.pyc
│     ├─ api_views.cpython-310.pyc
│     ├─ apps.cpython-310.pyc
│     ├─ apps.cpython-314.pyc
│     ├─ context_processors.cpython-310.pyc
│     ├─ models.cpython-310.pyc
│     ├─ models.cpython-314.pyc
│     ├─ serializers.cpython-310.pyc
│     ├─ urls.cpython-310.pyc
│     ├─ urls.cpython-314.pyc
│     ├─ views.cpython-310.pyc
│     ├─ views.cpython-314.pyc
│     ├─ __init__.cpython-310.pyc
│     └─ __init__.cpython-314.pyc
├─ recon_system
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  ├─ __init__.py
│  └─ __pycache__
│     ├─ settings.cpython-310.pyc
│     ├─ settings.cpython-314.pyc
│     ├─ urls.cpython-310.pyc
│     ├─ urls.cpython-314.pyc
│     ├─ wsgi.cpython-310.pyc
│     ├─ __init__.cpython-310.pyc
│     └─ __init__.cpython-314.pyc
└─ requirements.txt

```

## Installation

```bash
git clone <repo-url> recon_system
cd recon_system
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
```

## Running the App

```bash
python manage.py runserver
```

Open in browser:

| Page | URL |
|---|---|
| Admin Interface (default home) | http://127.0.0.1:8000/admin/ |
| Custom Web UI | http://127.0.0.1:8000/reconcile/ |
| API Docs (Swagger) | http://127.0.0.1:8000/api/docs/ |
| API Root | http://127.0.0.1:8000/api/ |

### Create Admin User (first time)

```bash
python manage.py createsuperuser
# follow prompts to set username, email, and password
```

## Usage

### Admin Interface (`/admin/`) — Default Home

Full management with Jazzmin dark theme:

- Custom dashboard with stat cards (configs, sessions, rules, results), recent sessions table, and quick action links.
- Create and manage **Configurations** with inline fields, mappings, and rules.
- Upload files via **Sessions** with status badges (Pending / Processing / Completed / Failed).
- View match rate percentages with color coding (green ≥80%, orange ≥50%, red <50%).
- Download matched, unmatched, and summary Excel exports directly from the session list.
- Failed sessions display error messages in a collapsible fieldset.

### Custom Web UI (`/reconcile/`)

Step-by-step wizard (embedded in Jazzmin layout):

1. **Configure Fields** — define field names, data types, Excel column mappings, and matching criteria (max 12 fields).
2. **Upload Files** — upload two Excel files (.xlsx / .xls) with the mapped columns.
3. **View Results** — see matched/unmatched records and download reports (matched, unmatched, summary).

### REST API (`/api/`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/` | GET | API overview |
| `/api/configs/` | GET/POST | List/create configurations |
| `/api/configs/{id}/` | GET/PUT/PATCH/DELETE | CRUD configuration |
| `/api/fields/` | GET/POST | List/create fields |
| `/api/mappings/` | GET/POST | List/create mappings |
| `/api/rules/` | GET/POST | List/create rules |
| `/api/sessions/` | GET/POST | List/create sessions |
| `/api/sessions/{id}/results/` | GET | Session results (filter by `?status=MATCH`) |
| `/api/sessions/{id}/download_matched/` | GET | Download matched Excel |
| `/api/sessions/{id}/download_unmatched/` | GET | Download unmatched Excel (multi-sheet) |
| `/api/sessions/{id}/download_summary/` | GET | Download summary Excel |
| `/api/results/` | GET/POST | List/create results |
| `/api/bulk-configure/` | POST | Create config + fields + mappings + rules in one call |
| `/api/reconcile/` | POST | Upload files and run reconciliation |
| `/api/schema/` | GET | OpenAPI schema (JSON) |
| `/api/docs/` | GET | Swagger UI documentation |

## App Components

### `reconcile` app

- `models.py` — 6 models: `ReconciliationConfig`, `ReconciliationField`, `FieldMapping`, `ReconciliationRule`, `ReconciliationSession`, `ReconciliationResult`. Session stores file paths as `CharField` (not `FileField`) plus display names and optional error messages.
- `serializers.py` — DRF serializers for all models, including `BulkConfigSerializer` and `ReconcileSerializer` for custom endpoints.
- `api_views.py` — ViewSets with full CRUD, filtering, search, pagination, plus custom `reconcile`, `bulk-configure`, and `download_*` actions.
- `api_urls.py` — API routing via DRF `DefaultRouter`.
- `admin.py` — Jazzmin-enhanced admin with inline editing, status badges, match rate colors, action buttons (download links), collapsible error fieldsets, and custom list displays.
- `context_processors.py` — Provides `dashboard_stats` context (config/session/rule/result counts, recent sessions) for the Jazzmin admin home.
- `views.py` — Custom web UI wizard (configure → upload → results), now embedded within the Jazzmin admin layout.
- `urls.py` — Custom web UI routes.

### Services

| Service | Description |
|---|---|
| `services/excel_parser.py` | Validate and read Excel files with pandas |
| `services/reconciliation.py` | Orchestrate file parsing, matching, and result persistence |
| `services/rule_engine.py` | Build match keys and compare records |
| `services/export_excel.py` | Generate Excel export responses |

### Utilities

| Utility | Description |
|---|---|
| `utils/dataframe.py` | DataFrame cleanup, header validation, serialization, and merging |

## Notes

- Uploaded Excel column headers must match the configured field mappings.
- File uploads are stored via Django default storage (paths stored as `CharField` in sessions).
- Results are persisted in SQLite by default.
- Maximum 12 fields per configuration, with at least 1 matching field required.
- Failed sessions capture error messages for debugging.
- The root URL (`/`) redirects to the admin interface.

## Suggested Improvements

- Add unit tests for service modules, serializers, and API views.
- Add Celery/background tasks for async file reconciliation.
- Support custom sheet selection for multi-sheet Excel workbooks.
- Add RBAC/permissions per config.
- Dockerize the application.

