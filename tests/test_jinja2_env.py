"""Tests for the Jinja2 environment factory."""

import pytest

from django_adminx.jinja2_env import (
    _admin_urlname,
    _admin_urlquote,
    _get_admin_log,
    _now,
    _url,
    _yesno,
    environment,
)


class TestEnvironmentFactory:
    def test_creates_environment(self):
        env = environment(autoescape=True)
        assert env is not None
        assert "static" in env.globals
        assert "url" in env.globals
        assert "now" in env.globals
        assert "get_admin_log" in env.globals
        assert "get_current_language" in env.globals

    def test_has_filters(self):
        env = environment(autoescape=True)
        assert "capfirst" in env.filters
        assert "yesno" in env.filters
        assert "admin_urlname" in env.filters
        assert "admin_urlquote" in env.filters

    def test_i18n_extension_loaded(self):
        env = environment(autoescape=True)
        assert "jinja2.ext.InternationalizationExtension" in env.extensions


class TestUrlGlobal:
    def test_resolves_admin_index(self):
        result = _url("admin:index")
        assert result == "/admin/"

    def test_raises_on_missing_view(self):
        from django.urls import NoReverseMatch

        with pytest.raises(NoReverseMatch):
            _url("nonexistent-view-name")

    def test_silent_returns_empty_on_missing_view(self):
        result = _url("nonexistent-view-name", silent=True)
        assert result == ""


class TestNowGlobal:
    def test_returns_utc_offset(self):
        result = _now("Z")
        # UTC offset like "+0000" or "+00:00"
        assert isinstance(result, str)
        assert len(result) > 0


class TestYesnoFilter:
    def test_true_value(self):
        assert _yesno(True, "yes,no,maybe") == "yes"

    def test_false_value(self):
        assert _yesno(False, "yes,no,maybe") == "no"

    def test_none_value(self):
        assert _yesno(None, "yes,no,maybe") == "maybe"

    def test_none_without_maybe(self):
        assert _yesno(None, "yes,no") == "no"

    def test_default_arg(self):
        assert _yesno(True) == "yes"
        assert _yesno(False) == "no"


class TestAdminUrlnameFilter:
    def test_returns_url_name(self):

        class FakeOpts:
            app_label = "auth"
            model_name = "user"

        result = _admin_urlname(FakeOpts(), "changelist")
        assert result == "admin:auth_user_changelist"


class TestAdminUrlquoteFilter:
    def test_quotes_special_chars(self):
        assert _admin_urlquote("hello world") == "hello%20world"

    def test_preserves_safe_chars(self):
        assert _admin_urlquote("hello") == "hello"


@pytest.mark.django_db
class TestGetAdminLog:
    def test_returns_empty_for_no_entries(self):
        result = _get_admin_log(10)
        assert list(result) == []

    def test_respects_limit(self):
        result = _get_admin_log(5)
        assert result.query.is_sliced
