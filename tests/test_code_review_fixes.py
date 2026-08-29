"""Tests for issues found in the full-package code review."""

from __future__ import annotations

from pathlib import Path

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from django_admin_boost import admin
from django_admin_boost.admin import ModelAdmin
from tests.testapp.models import Article


class DocstringAccuracyTest(TestCase):
    """Issues #4 and #5: docstrings must reference correct module paths."""

    def test_jinja2_env_docstring_has_correct_path(self):
        """Issue #4: jinja2_env.environment docstring must use 'django_admin_boost.admin.jinja2_env.environment'."""
        from django_admin_boost.admin.jinja2_env import environment

        docstring = environment.__doc__
        assert "django_admin_boost.admin.jinja2_env.environment" in docstring, (
            f"Docstring contains wrong path. Expected 'django_admin_boost.admin.jinja2_env.environment' but got: {docstring}"
        )
        assert "django_admin_boost.jinja2_env.environment" not in docstring.replace(
            "django_admin_boost.admin.jinja2_env.environment",
            "",
        ), "Docstring still contains the wrong path 'django_admin_boost.jinja2_env.environment'"

    def test_top_level_init_docstring_has_correct_module(self):
        """Issue #5: __init__.py docstring must reference 'django_admin_boost.admin', not 'django_admin_boost.adminx'."""
        import django_admin_boost

        docstring = django_admin_boost.__doc__
        assert "django_admin_boost.admin" in docstring
        assert "django_admin_boost.adminx" not in docstring, (
            "Docstring references non-existent module 'django_admin_boost.adminx'. Should be 'django_admin_boost.admin'."
        )


class UUIDFallbackDetectionTest(TestCase):
    """Issue #7: _is_changelist_request fallback must detect UUID PKs."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.superuser = User.objects.create_superuser(username="admin", password="password")

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.site = admin.AdminSite()

        class TestArticleAdmin(ModelAdmin):
            list_only_fields = ["id", "title"]

        self.model_admin = TestArticleAdmin(Article, self.site)

    def test_uuid_pk_detected_as_change_view(self):
        """A UUID PK in the URL path should be detected as a change view (not changelist)."""
        request = self.factory.get("/admin/testapp/article/550e8400-e29b-41d4-a716-446655440000/change/")
        # Deliberately remove resolver_match to exercise fallback path
        request.resolver_match = None
        result = self.model_admin._is_changelist_request(request)
        assert result is False, "UUID PK path should be detected as change view, not changelist"

    def test_uuid_pk_without_change_suffix_detected(self):
        """A URL ending with a UUID PK (no /change/ suffix) should be detected as a change view."""
        request = self.factory.get("/admin/testapp/article/550e8400-e29b-41d4-a716-446655440000/")
        request.resolver_match = None
        result = self.model_admin._is_changelist_request(request)
        assert result is False, "URL ending with UUID PK should be detected as change view"

    def test_digit_pk_still_detected(self):
        """Numeric PKs should still be detected as change views in fallback."""
        request = self.factory.get("/admin/testapp/article/42/")
        request.resolver_match = None
        result = self.model_admin._is_changelist_request(request)
        assert result is False

    def test_changelist_path_returns_true(self):
        """A changelist path should return True in fallback."""
        request = self.factory.get("/admin/testapp/article/")
        request.resolver_match = None
        result = self.model_admin._is_changelist_request(request)
        assert result is True


class AdminLocaleTest(TestCase):
    """Issue #2: Django admin translations must still be loadable."""

    def test_django_admin_locale_path_is_discoverable(self):
        """The Django admin locale directory must be in LOCALE_PATHS or discoverable."""
        import django

        django_admin_locale = Path(django.__file__).parent / "contrib" / "admin" / "locale"
        assert django_admin_locale.is_dir(), "Django admin locale dir not found"

        # After adminx replaces django.contrib.admin, the admin locale must
        # still be discoverable via LOCALE_PATHS
        from django.conf import settings

        locale_paths = list(getattr(settings, "LOCALE_PATHS", []))

        # Also check app locale paths (what Django's all_locale_paths() does)
        from django.apps import apps

        app_locale_paths = []
        for app_config in apps.get_app_configs():
            app_locale = Path(app_config.path) / "locale"
            if app_locale.is_dir():
                app_locale_paths.append(str(app_locale))

        all_paths = locale_paths + app_locale_paths

        assert any(Path(p).resolve() == django_admin_locale.resolve() for p in all_paths if Path(p).is_dir()), (
            f"Django's admin locale ({django_admin_locale}) is not discoverable. "
            f"It must be in LOCALE_PATHS or in an app's locale/ directory. "
            f"Current discoverable paths: {all_paths}"
        )
