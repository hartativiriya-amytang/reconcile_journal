# Recon System

## Overview

`recon_system` is a Django-based reconciliation application built to compare two Excel datasets and highlight matched versus unmatched records. It supports configurable reconciliation fields, matching rules, session persistence, and Excel export of results.

## Features

- Configure reconciliation fields and matching criteria.
- Upload and parse Excel files (`.xlsx`, `.xls`).
- Match records from File A and File B using configurable keys.
- Store reconciliation sessions and detailed results.
- Export matched, unmatched, and summary reports as Excel files.

## Project Structure

```
recon_system
├─ db.sqlite3
├─ manage.py
├─ README.md
├─ reconcile
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ services
│  │  ├─ excel_parser.py
│  │  ├─ export_excel.py
│  │  ├─ reconciliation.py
│  │  ├─ rule_engine.py
│  ├─ templates
│  │  └─ reconcile
│  │     ├─ base.html
│  │     ├─ configure_fields.html
│  │     ├─ index.html
│  │     ├─ uploads_file.html
│  │     └─ view_results.html
│  ├─ templatetags
│  │  └─ dict_filters.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ utils
│  │  └─ dataframe.py
│  ├─ views.py
│  └─ __init__.py
└─ recon_system
   ├─ asgi.py
   ├─ settings.py
   ├─ urls.py
   ├─ wsgi.py
   └─ __init__.py
```

## Requirements

- Python 3.10+
- Django 5.2
- pandas
- openpyxl

## Installation

1. Clone or open the repository.
2. Create and activate a virtual environment.

```bash
cd c:\Users\amyta\Documents\recon_system
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install django pandas openpyxl
```

4. Apply database migrations.

```bash
python manage.py makemigrations
python manage.py migrate
```

## Running the App

Start the Django development server:

```bash
python manage.py runserver
```

Open the application in a browser at:

```text
http://127.0.0.1:8000/
```

## Usage

1. From the home screen, create a new reconciliation configuration.
2. Define up to 12 fields and choose which fields are used for matching.
3. Upload File A and File B as Excel workbooks.
4. The system processes the files and generates a reconciliation session.
5. View results and download matched, unmatched, and summary Excel exports.

## App Components

### `reconcile` app

This app contains the main reconciliation logic:

- `models.py`
  - `ReconciliationConfig`: stores reconciliation configurations.
  - `ReconciliationField`: stores configured fields and matching criteria.
  - `ReconciliationSession`: records each upload and reconciliation run.
  - `ReconciliationResult`: stores individual matched and unmatched records.

- `views.py`
  - `index`: displays recent reconciliation sessions.
  - `configure_fields`: creates and saves reconciliation field configurations.
  - `upload_files`: uploads Excel files, validates them, and runs reconciliation.
  - `view_results`: displays reconciliation results and provides export actions.
  - `download_matched`, `download_unmatched`, `download_summary`: export results as Excel files.
  - `get_config_status`: simple JSON endpoint to verify config state.

- `urls.py`
  - Defines app routing for web pages and download endpoints.

- `templates/reconcile`
  - `base.html`: base layout for the UI.
  - `index.html`: home page and session list.
  - `configure_fields.html`: field configuration form.
  - `uploads_file.html`: file upload page.
  - `view_results.html`: reconciliation result dashboard.

- `admin.py`
  - Registers reconciliation models for Django admin management.

### `reconcile/services/excel_parser.py`

This service validates and reads Excel files using `pandas`:

- `validate_excel_file()`: checks allowed Excel file extensions.
- `read_excel_file()`: reads a sheet into a DataFrame, trims whitespace, and drops empty rows.
- `get_sheet_names()`: exposes available workbook sheets.
- `map_columns()`: maps incoming Excel columns to configured system fields.
- `convert_data_types()`: converts fields to `number`, `date`, or `datetime` as configured.
- `clean_headers()`: normalizes header values.

### `reconcile/services/rule_engine.py`

This engine computes matching keys and performs record matching:

- `generate_match_key()`: builds a deterministic hash from configured matching fields.
- `is_match()`: compares two records field-by-field with normalized string comparison.
- `reconcile_data()`: matches records from File A and File B, returning matched, only-A, and only-B lists.

### `reconcile/services/reconciliation.py`

This is the orchestration service that ties parsing and rule evaluation together:

- Validates both uploaded files.
- Reads and maps file contents to configured fields.
- Cleans input data and drops empty matching rows.
- Converts mapped rows to JSON-serializable dictionaries.
- Uses `RuleEngine` to compare data and categorize records.
- Returns summary counts and matched/unmatched payloads.
- Persists results to `ReconciliationResult` records for each session.

### `reconcile/services/export_excel.py`

Provides Excel export helpers for matched, unmatched, and summary reports.

- `_create_excel_response()`: returns an `HttpResponse` with an Excel file.
- `export_matched_data()`: exports matched rows from both files.
- `export_unmatched_data()`: exports unmatched rows with separate sheets.
- `export_summary()`: exports session summary metrics.

### `reconcile/utils/dataframe.py`

Utility functions for DataFrame cleanup and validation:

- `clean_dataframe()`: trims whitespace, drops empty rows, and normalizes empty strings.
- `validate_headers()`: checks if the DataFrame contains required column headers.
- `get_missing_headers()`: returns header names that are not present.
- `convert_to_serializable()`: converts a DataFrame to JSON-safe dictionary records.
- `merge_dataframes()`: merges two DataFrames and annotates match status.
- `get_match_summary()`: summarizes reconciliation results in a DataFrame.

## Notes

- The current implementation assumes uploaded Excel column headers match the configured field names.
- File uploads are stored temporarily via Django default storage.
- Results are persisted in SQLite by default.

## Suggested Improvements

- Add a `requirements.txt` file for explicit dependencies.
- Add unit tests for service modules and views.
- Support custom field-to-column mapping for arbitrary Excel headers.
- Add pagination for long result sets.
- Add user authentication and multi-user session support.

## Contact

Inspect `reconcile/views.py`, `reconcile/services/`, and `reconcile/models.py` for the main implementation details.
