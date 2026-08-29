"""Performance-oriented ModelAdmin mixins."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured

from django_admin_boost.paginators import EstimatedCountPaginator

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


class ListFieldsMixin:
    """
    ModelAdmin mixin that optimises changelist querysets by limiting fetched columns.

    Three modes of operation:

    1. **Explicit whitelist** — set ``list_only_fields`` to a list of field names.
       The queryset will use ``.only(pk, *list_only_fields)``.
       An empty list means ``.only(pk)``.

    2. **Explicit blacklist** — set ``list_defer_fields`` to a list of field names.
       The queryset will use ``.defer(*list_defer_fields)``.
       An empty list disables the optimisation entirely (opt-out escape hatch).

    3. **Auto mode** (default) — when neither attribute is set, ``list_display``
       is inspected to determine which concrete model fields are needed, and
       ``.only(pk, *resolved_fields)`` is applied.

    Setting both ``list_only_fields`` and ``list_defer_fields`` raises
    ``ImproperlyConfigured``.

    The optimisation is only applied on changelist requests; add/change views
    always get the full queryset.

    Example::

        class BookAdmin(ListFieldsMixin, admin.ModelAdmin):
            list_only_fields = ["id", "title", "status", "created_at"]
    """

    list_only_fields: list[str] | None = None
    list_defer_fields: list[str] | None = None

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs: QuerySet[Any] = super().get_queryset(request)  # type: ignore[misc]

        if not self._is_changelist_request(request):
            return qs

        if self.list_only_fields is not None and self.list_defer_fields is not None:
            raise ImproperlyConfigured(
                f"Cannot set both list_only_fields and list_defer_fields on "
                f"{self.__class__.__name__}. Use one or the other.",
            )

        if self.list_only_fields is not None:
            pk_name = self.opts.pk.name  # type: ignore[attr-defined]
            fields = {pk_name, *self.list_only_fields}
            qs = qs.only(*fields)
        elif self.list_defer_fields is not None:
            if not self.list_defer_fields:
                return qs  # empty list = opt-out
            qs = qs.defer(*self.list_defer_fields)
        else:
            # Auto mode: resolve list_display to concrete fields
            fields = self._resolve_list_display_fields()
            qs = qs.only(*fields)

        # Auto select_related for FK fields in list_display
        list_select_related = getattr(self, "list_select_related", False)
        if list_select_related is False:
            # Auto-detect
            select_related = self._resolve_select_related()
            if select_related:
                qs = qs.select_related(*select_related)
        # If list_select_related is True or a list, Django/user handles it

        return qs

    def _resolve_list_display_fields(self) -> set[str]:
        """Resolve ``list_display`` entries to concrete model field names."""
        pk_name = self.opts.pk.name  # type: ignore[attr-defined]
        fields = {pk_name}

        for entry in self.list_display:  # type: ignore[attr-defined]
            if entry == "__str__":
                # __str__ contributes only pk
                continue
            if callable(entry) and not isinstance(entry, str):
                # A callable object (not a string) — skip
                continue
            if isinstance(entry, str):
                # Check if it's a concrete model field
                try:
                    field = self.opts.get_field(entry)  # type: ignore[attr-defined]
                except Exception:  # noqa: BLE001
                    # Not a model field — could be a method on the ModelAdmin
                    # or model. Check if it's a method on self.
                    if hasattr(self, entry) and callable(getattr(self, entry)):
                        continue
                    # Could be a model method/property — skip
                    continue
                # For ForeignKey fields, Django stores the _id column
                if hasattr(field, "attname"):
                    fields.add(field.attname)
                else:
                    fields.add(entry)

        return fields

    def _resolve_select_related(self) -> list[str]:
        """Auto-detect FK fields in list_display that need select_related."""
        related = []
        for entry in self.list_display:  # type: ignore[attr-defined]
            if not isinstance(entry, str):
                continue
            # Check for dotted paths like "category__name"
            if "__" in entry:
                prefix = entry.split("__")[0]
                if prefix:  # skip entries like "__str__" that start with "__"
                    related.append(prefix)
                continue
            # Check if it's a FK field
            try:
                field = self.opts.get_field(entry)  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001, S112
                continue
            if hasattr(field, "is_relation") and field.is_relation and field.many_to_one:
                related.append(entry)
        return related

    def _is_changelist_request(self, request: HttpRequest) -> bool:
        """Return True when *request* targets the changelist (not add/change)."""
        resolver = getattr(request, "resolver_match", None)
        if resolver is not None:
            url_name: str = resolver.url_name or ""
            return url_name.endswith("_changelist")

        path = request.path
        if path.endswith(("/add/", "/change/")):
            return False
        parts = [p for p in path.rstrip("/").split("/") if p]
        if parts:
            last = parts[-1]
            if last.isdigit() or _UUID_RE.match(last):
                return False
        return True


class SmartPaginatorMixin:
    """
    ModelAdmin mixin that uses :class:`~django_admin_boost.paginators.EstimatedCountPaginator`.

    On PostgreSQL this avoids expensive ``COUNT(*)`` queries for unfiltered
    changelist views by reading the row estimate from ``pg_class.reltuples``.

    ``show_full_result_count`` is set to ``False`` because the count is an
    estimate and displaying "1000 results (1000 total)" would be misleading.
    """

    paginator: type[EstimatedCountPaginator] = EstimatedCountPaginator
    show_full_result_count = False
