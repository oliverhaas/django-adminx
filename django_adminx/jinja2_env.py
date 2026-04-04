"""Jinja2 environment factory for Django admin templates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import jinja2
from django.contrib.admin.models import LogEntry
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.dateformat import format as dateformat
from django.utils.text import capfirst
from django.utils.translation import get_language, get_language_bidi, gettext, ngettext


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
            "get_current_language": get_language,
            "get_current_language_bidi": get_language_bidi,
            "get_admin_log": _get_admin_log,
            "now": _now,
            "static": static,
            "url": _url,
        },
    )

    env.filters.update(
        {
            "admin_urlname": _admin_urlname,
            "admin_urlquote": _admin_urlquote,
            "capfirst": capfirst,
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


def _admin_urlquote(value: str) -> str:
    """URL-encode a value for use in admin URLs."""
    return quote(value)


def _urlencode_path(value: str) -> str:
    """Percent-encode a path for use in URL comparisons."""
    return quote(str(value), safe="/")
