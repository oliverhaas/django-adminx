"""Jinja2 environment factory for Django admin templates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import jinja2
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.dateformat import format as dateformat
from django.utils.encoding import iri_to_uri
from django.utils.formats import date_format, localize
from django.utils.html import conditional_escape
from django.utils.text import Truncator, capfirst
from django.utils.translation import get_language, get_language_bidi, gettext, ngettext
from markupsafe import Markup

from django_adminx.jinja2_helpers import select_admin_template
from django_adminx.models import LogEntry
from django_adminx.templatetags.admin_list import (
    admin_actions as _raw_admin_actions,
)
from django_adminx.templatetags.admin_list import (
    admin_list_filter,
    date_hierarchy,
    pagination,
    paginator_number,
    result_headers,
    result_hidden_fields,
    result_list,
    results,
    search_form,
)
from django_adminx.templatetags.admin_modify import (
    cell_count,
)
from django_adminx.templatetags.admin_modify import (
    prepopulated_fields_js as _raw_prepopulated_fields_js,
)
from django_adminx.templatetags.admin_modify import (
    submit_row as _raw_submit_row,
)
from django_adminx.templatetags.admin_urls import (
    add_preserved_filters as _raw_add_preserved_filters,
)


def environment(**options: object) -> jinja2.Environment:
    """Create a Jinja2 environment configured for Django admin templates.

    Usage in settings::

        TEMPLATES = [{
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "APP_DIRS": True,
            "OPTIONS": {
                "environment": "django_adminx.jinja2_env.environment",
                ...
            },
        }]
    """
    env = jinja2.Environment(**options)  # type: ignore[arg-type]  # noqa: S701
    env.add_extension("jinja2.ext.i18n")
    env.install_gettext_callables(gettext, ngettext, newstyle=True)  # type: ignore[attr-defined]

    env.globals.update(
        {
            # Core helpers
            "get_current_language": get_language,
            "get_current_language_bidi": get_language_bidi,
            "get_admin_log": _get_admin_log,
            "now": _now,
            "static": static,
            "url": _url,
            # Template hierarchy helper
            "select_admin_template": select_admin_template,
            # admin_list templatetag functions (context-aware wrappers)
            "admin_actions": _admin_actions_jinja2,
            "admin_list_filter": admin_list_filter,
            "date_hierarchy": date_hierarchy,
            "pagination": pagination,
            "paginator_number": paginator_number,
            "result_headers": result_headers,
            "result_hidden_fields": result_hidden_fields,
            "result_list": result_list,
            "results": results,
            "search_form": search_form,
            # admin_modify templatetag functions (context-aware wrappers)
            "prepopulated_fields_js": _prepopulated_fields_js_jinja2,
            "submit_row": _submit_row_jinja2,
            # admin_urls templatetag functions
            "add_preserved_filters": _add_preserved_filters_jinja2,
        },
    )

    env.filters.update(
        {
            "admin_urlname": _admin_urlname,
            "admin_urlquote": _admin_urlquote,
            "capfirst": capfirst,
            "iriencode": _iriencode,
            "cell_count": cell_count,
            "date": _date_filter,
            "truncatewords": _truncatewords,
            "unlocalize": _unlocalize,
            "unordered_list": _unordered_list,
            "urlencode_path": _urlencode_path,
            "yesno": _yesno,
        },
    )

    return env


# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------


def _url(viewname: str, *args: object, silent: bool = False, **kwargs: object) -> str:
    """Wrap ``reverse()``, optionally catching ``NoReverseMatch``."""
    try:
        return reverse(viewname, args=args, kwargs=kwargs)
    except NoReverseMatch:
        if silent:
            return ""
        raise


def _now(format_string: str) -> str:
    """Return the current datetime formatted with Django's dateformat."""
    return dateformat(datetime.now(tz=UTC), format_string)


def _get_admin_log(limit: int = 10, user: object = None) -> object:
    """Return recent ``LogEntry`` objects, optionally filtered by user."""
    qs = LogEntry.objects.select_related("content_type", "user")
    if user is not None and not getattr(user, "is_anonymous", True):
        qs = qs.filter(user=user)  # type: ignore[misc]
    return qs[:limit]


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


def _yesno(value: object, arg: str = "yes,no,maybe") -> str:
    """Port of Django's ``yesno`` template filter."""
    bits = arg.split(",")
    if len(bits) < 2:  # noqa: PLR2004
        return str(value)
    yes, no = bits[0], bits[1]
    maybe = bits[2] if len(bits) > 2 else bits[1]  # noqa: PLR2004
    if value is None:
        return maybe
    if value:
        return yes
    return no


def _admin_urlname(value: Any, arg: str) -> str:  # noqa: ANN401
    """Return the admin URL name for a model's action.

    ``value`` is expected to be a model ``Options`` (``_meta``) object.
    """
    return "admin:%s_%s_%s" % (value.app_label, value.model_name, arg)  # noqa: UP031


def _admin_urlquote(value: object) -> str:
    """URL-encode a value for use in admin URLs."""
    return quote(str(value))


def _iriencode(value: str) -> str:
    """Port of Django's ``iriencode`` template filter."""
    return iri_to_uri(value)


def _jinja2_context_to_dict(context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Convert a Jinja2 Context (immutable) to a plain dict for Django templatetags."""
    if isinstance(context, dict):
        return context
    return dict(context)


@jinja2.pass_context
def _admin_actions_jinja2(context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Jinja2 wrapper for admin_actions that auto-injects context."""
    ctx = _jinja2_context_to_dict(context)
    return _raw_admin_actions(ctx)


@jinja2.pass_context
def _submit_row_jinja2(context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Jinja2 wrapper for submit_row that auto-injects context."""
    ctx = _jinja2_context_to_dict(context)
    return _raw_submit_row(ctx)


@jinja2.pass_context
def _prepopulated_fields_js_jinja2(context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Jinja2 wrapper for prepopulated_fields_js that auto-injects context."""
    ctx = _jinja2_context_to_dict(context)
    return _raw_prepopulated_fields_js(ctx)


@jinja2.pass_context
def _add_preserved_filters_jinja2(
    context: Any,  # noqa: ANN401
    url: str,
    popup: bool = False,  # noqa: FBT001,FBT002
    to_field: str | None = None,
) -> str:
    """Jinja2 wrapper for add_preserved_filters that auto-injects context."""
    ctx = _jinja2_context_to_dict(context)
    return _raw_add_preserved_filters(ctx, url, popup, to_field)


def _urlencode_path(value: str) -> str:
    """Percent-encode a path for use in URL comparisons."""
    return quote(str(value), safe="/")


def _date_filter(value: Any, arg: str = "DATETIME_FORMAT") -> str:  # noqa: ANN401
    """Port of Django's ``date`` template filter."""
    if value is None:
        return ""
    return date_format(value, arg)


def _truncatewords(value: str, arg: int | str = 15) -> str:
    """Port of Django's ``truncatewords`` template filter."""
    try:
        length = int(arg)
    except (ValueError, TypeError):
        return str(value)
    return Truncator(value).words(length, truncate=" \u2026")


def _unlocalize(value: Any) -> str:  # noqa: ANN401
    """Port of Django's ``unlocalize`` template filter.

    Forces a value into its non-localized string representation.
    """
    return str(localize(value, use_l10n=False))


def _unordered_list(value: list[Any]) -> str:
    """Port of Django's ``unordered_list`` template filter.

    Recursively takes a self-nested list and returns an HTML unordered list
    (without the opening/closing ``<ul>`` tags).
    """

    def _helper(items: list[Any]) -> list[str]:
        output: list[str] = []
        for item in items:
            if isinstance(item, (list, tuple)):
                if output:
                    last = output.pop()
                    last = last.removesuffix("</li>")
                    output.append(last)
                    output.append("<ul>")
                    output.extend(_helper(list(item)))
                    output.append("</ul>")
                    output.append("</li>")
                else:
                    output.append("<ul>")
                    output.extend(_helper(list(item)))
                    output.append("</ul>")
            else:
                output.append(f"<li>{conditional_escape(item)}</li>")
        return output

    return Markup("\n".join(_helper(value)))  # noqa: S704
