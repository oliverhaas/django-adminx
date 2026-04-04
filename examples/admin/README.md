# Admin Example

A small shop project to exercise django-adminx with the Jinja2 admin templates.

## Setup

```bash
cd examples/admin
uv run python manage.py migrate
uv run python seed.py
uv run python manage.py runserver
```

Then open http://localhost:8000/admin/ and log in with **admin / admin**.

## What's in the box

- **Categories** — simple model with list_editable sort order
- **Tags** — minimal model (just a name)
- **Products** — the kitchen sink: FK, M2M, choices, date_hierarchy, fieldsets, inlines, search, filters, list_only_fields
- **Customers** — search, readonly fields
- **Orders** — FK to customer, status filter, date_hierarchy, inline order items
