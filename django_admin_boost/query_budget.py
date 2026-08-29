from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import connection, reset_queries

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class QueryBudgetExceeded(Exception):  # noqa: N818
    """Raised when a view exceeds its query budget."""

    def __init__(self, budget: int, actual: int, queries: list[dict[str, str]]) -> None:
        self.budget = budget
        self.actual = actual
        self.queries = queries
        super().__init__(
            f"Query budget exceeded: {actual} queries (budget: {budget})",
        )


class QueryBudgetMixin:
    """ModelAdmin mixin that enforces a maximum query count on changelist views.

    Only active when ``DEBUG=True``. Set ``query_budget`` on your ModelAdmin
    to enforce a limit::

        class MyAdmin(QueryBudgetMixin, admin.ModelAdmin):
            query_budget = 10

    When exceeded, raises ``QueryBudgetExceeded`` with the list of queries
    for debugging. Set ``query_budget_warn_only = True`` to log a warning
    instead of raising.
    """

    query_budget: int | None = None
    query_budget_warn_only: bool = False

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        if not self._should_check_budget():
            return super().changelist_view(request, extra_context=extra_context)  # type: ignore[misc]

        reset_queries()
        response = super().changelist_view(request, extra_context=extra_context)  # type: ignore[misc]
        self._check_budget(connection.queries[:])
        return response

    def _should_check_budget(self) -> bool:
        return self.query_budget is not None and settings.DEBUG

    def _check_budget(self, queries: list[dict[str, str]]) -> None:
        actual = len(queries)
        if actual <= self.query_budget:  # type: ignore[operator]
            return

        if self.query_budget_warn_only:
            logger.warning(
                "Query budget exceeded for %s: %d queries (budget: %d)",
                self.__class__.__name__,
                actual,
                self.query_budget,
            )
            return

        raise QueryBudgetExceeded(self.query_budget, actual, queries)  # type: ignore[arg-type]
