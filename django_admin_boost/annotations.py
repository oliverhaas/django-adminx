from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Expression


class AnnotatedField:
    """Declarative annotation for use in list_display.

    Usage::

        from django.db.models import Count
        from django_admin_boost.annotations import AnnotatedField

        class MyAdmin(ModelAdmin):
            list_display = ["name", AnnotatedField("tag_count", Count("tags"), short_description="Tags")]
    """

    def __init__(
        self,
        name: str,
        expression: Expression,
        short_description: str | None = None,
        empty_value: str = "-",
    ) -> None:
        self.name = name
        self.expression = expression
        self.short_description = short_description or name.replace("_", " ").title()
        self.empty_value = empty_value
        # Make this work as a list_display callable
        self.admin_order_field = name

    def __call__(self, obj: object) -> object:
        value = getattr(obj, self.name, None)
        if value is None:
            return self.empty_value
        return value

    def __repr__(self) -> str:
        return f"AnnotatedField({self.name!r})"
