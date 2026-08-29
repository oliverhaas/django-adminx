"""django-admin-boost: Performance-oriented Django admin extensions.

Standalone mixins and paginators that work with stock django.contrib.admin.
For the full Jinja2-compatible admin replacement, use ``django_admin_boost.admin``.
"""

from django_admin_boost.mixins import ListFieldsMixin, SmartPaginatorMixin
from django_admin_boost.paginators import EstimatedCountPaginator
from django_admin_boost.query_budget import QueryBudgetMixin

__all__ = [
    "EstimatedCountPaginator",
    "ListFieldsMixin",
    "QueryBudgetMixin",
    "SmartPaginatorMixin",
]
