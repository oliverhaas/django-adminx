"""django-admin-boost: Performance-oriented Django admin extensions.

Standalone mixins and paginators that work with stock django.contrib.admin.
For the full Jinja2-compatible admin replacement, use ``django_admin_boost.admin``.
"""

from django_admin_boost.annotations import AnnotatedField
from django_admin_boost.mixins import ListFieldsMixin, SmartPaginatorMixin
from django_admin_boost.paginators import EstimatedCountPaginator

__all__ = [
    "AnnotatedField",
    "EstimatedCountPaginator",
    "ListFieldsMixin",
    "SmartPaginatorMixin",
]
