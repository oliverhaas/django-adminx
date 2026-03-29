---
status: idea
effort: medium
impact: high
---

# django-adminx

Performance-oriented Django admin extensions. Drop-in compatible with the standard admin — no rewrites, no vendor lock-in.

## Problem

Django's admin is convenient but makes poor default choices for performance at scale: full model instances on list views, COUNT(*) for pagination on large tables, no guidance on query budgets. Replacing the admin entirely (e.g. django-smartbase-admin) fixes some of this but breaks compatibility with the ecosystem.

## Scope

A `BaseModelAdmin` mixin (or set of mixins) that layers performance optimizations on top of the standard admin, keeping full compatibility with existing `ModelAdmin` code, templates, and third-party packages.

### list_only_fields

Automatic `.only()` on list view querysets. Declare which fields the list view actually needs:

```python
class MyAdmin(BaseModelAdmin):
    list_only_fields = ["id", "name", "status", "created_at"]
```

Overrides `get_queryset()` to apply `.only()` on changelist views. Paired with query-count tests to catch deferred-field regressions (a callable or `__str__` silently accessing an excluded field bumps the count).

### Smart paginator (postgres reltuples)

Replace the default paginator's `COUNT(*)` with `pg_class.reltuples` for unfiltered querysets on large PostgreSQL tables. Falls back to real count when filters are active or the estimate is stale.

### Future ideas (SBAdmin-inspired, compatibility-first)

- Auto `select_related` / `prefetch_related` from `list_display` / `list_filter` introspection
- Per-view query budget assertions (dev/test mode)
- Annotation helpers that integrate with `list_display` sorting and filtering

## Prior art

- django-smartbase-admin -- full admin replacement with annotate/values pipeline, not compatible with standard admin
- Django's `show_full_result_count` -- blunt on/off toggle, no estimation
- django-postgres-stats -- stats utilities but not admin-integrated
