#project structure
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
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  │     ├─ 0001_initial.cpython-310.pyc
│  │     └─ __init__.cpython-310.pyc
│  ├─ models.py
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
│  ├─ templates
│  │  └─ reconcile
│  │     ├─ base.html
│  │     ├─ configure_fields.html
│  │     ├─ index.html
│  │     ├─ uploads_file.html
│  │     └─ view_results.html
│  ├─ templatetags
│  │  ├─ dict_filters.py
│  │  └─ __pycache__
│  │     └─ dict_filters.cpython-310.pyc
│  ├─ tests.py
│  ├─ urls.py
│  ├─ utils
│  │  └─ dataframe.py
│  ├─ views.py
│  ├─ __init__.py
│  └─ __pycache__
│     ├─ admin.cpython-310.pyc
│     ├─ apps.cpython-310.pyc
│     ├─ models.cpython-310.pyc
│     ├─ urls.cpython-310.pyc
│     ├─ views.cpython-310.pyc
│     └─ __init__.cpython-310.pyc
└─ recon_system
   ├─ asgi.py
   ├─ settings.py
   ├─ urls.py
   ├─ wsgi.py
   ├─ __init__.py
   └─ __pycache__
      ├─ settings.cpython-310.pyc
      ├─ urls.cpython-310.pyc
      ├─ wsgi.cpython-310.pyc
      └─ __init__.cpython-310.pyc

```