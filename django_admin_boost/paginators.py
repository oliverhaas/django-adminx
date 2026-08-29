"""Performance-oriented paginator for Django admin."""

from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.db import connections
from django.db.models import QuerySet
from django.utils.functional import cached_property


class EstimatedCountPaginator(Paginator):
    """
    Paginator that uses PostgreSQL's ``pg_class.reltuples`` for fast row
    estimates on unfiltered querysets.

    On large tables the default ``COUNT(*)`` can be extremely slow.  PostgreSQL
    maintains a row-count estimate in the ``pg_class`` catalogue table that is
    updated by ``VACUUM`` and ``ANALYZE``.  This paginator reads that estimate
    when it is safe to do so and falls back to a real ``COUNT(*)`` otherwise.

    Fallback conditions (any one triggers a real count):
    * The database backend is not PostgreSQL.
    * The queryset has WHERE clauses (i.e. admin filters are active).
    * The estimate is ≤ 0 (table freshly created / never analysed).
    """

    _used_estimate: bool = False

    @cached_property
    def count(self) -> int:
        """Return the total number of objects, using an estimate when possible."""
        queryset = self.object_list

        if not isinstance(queryset, QuerySet):
            return len(self.object_list)

        if self._can_use_estimate(queryset):
            estimate = self._get_estimate(queryset)
            if estimate is not None and estimate > 0:
                self._used_estimate = True
                return int(estimate)

        # Strip display-only annotations for a lighter count query
        return self._smart_count(queryset)

    def _smart_count(self, queryset: QuerySet) -> int:
        """Count rows, stripping annotations not needed for filtering/ordering."""
        annotations_in_use = self._get_referenced_annotations(queryset)
        all_annotations = set(queryset.query.annotations.keys())
        display_only = all_annotations - annotations_in_use

        if display_only:
            # Create a stripped queryset for counting
            count_qs = queryset.all()  # clone
            for name in display_only:
                count_qs.query.annotations.pop(name, None)
            # Recalculate group_by after removing annotations; otherwise Django
            # may issue a flat COUNT(*) over the join and return wrong results.
            count_qs.query.set_group_by()
            return count_qs.count()

        return queryset.count()

    def _get_referenced_annotations(self, queryset: QuerySet) -> set[str]:
        """Return annotation names referenced by WHERE or ORDER BY clauses."""
        referenced = set()

        # Check WHERE clause
        where_sql = str(queryset.query.where)
        for name in queryset.query.annotations:
            if name in where_sql:
                referenced.add(name)

        # Check ORDER BY
        for ordering in queryset.query.order_by:
            if not isinstance(ordering, str):
                continue
            clean_name = ordering.lstrip("-")
            if clean_name in queryset.query.annotations:
                referenced.add(clean_name)

        return referenced

    @property
    def is_approximate_count(self) -> bool:
        """Return True if the count was derived from an estimate, not an exact query."""
        _ = self.count  # ensure count is computed
        return self._used_estimate

    def _can_use_estimate(self, queryset: QuerySet[Any]) -> bool:
        """Return True if we can safely use pg_class.reltuples."""
        connection = connections[queryset.db]
        if connection.vendor != "postgresql":
            return False

        # Check for WHERE clauses — if the queryset is filtered, the estimate
        # would be inaccurate.
        return not queryset.query.where

    def _get_estimate(self, queryset: QuerySet[Any]) -> float | None:
        """Read the row-count estimate from pg_class.reltuples."""
        model = queryset.query.model
        assert model is not None  # noqa: S101
        table_name = model._meta.db_table  # noqa: SLF001
        connection = connections[queryset.db]

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples FROM pg_class WHERE relname = %s",
                [table_name],
            )
            row = cursor.fetchone()

        if row is None:
            return None
        return row[0]
