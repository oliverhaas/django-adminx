import importlib

import pytest
from django.contrib.admin import site as admin_site
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import clear_url_caches, set_urlconf

from django_admin_boost.admin import ModelAdmin
from django_admin_boost.query_budget import QueryBudgetExceeded, QueryBudgetMixin
from tests.testapp.admin import ArticleAdmin
from tests.testapp.models import Article


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin", password="password")


@pytest.fixture
def articles(db):
    return [Article.objects.create(title=f"Article {i}") for i in range(5)]


def _register(model_admin_class):
    """Register model_admin_class for Article and refresh URL patterns."""
    if admin_site.is_registered(Article):
        admin_site.unregister(Article)
    admin_site.register(Article, model_admin_class)
    _refresh_urls()


def _restore():
    """Restore ArticleAdmin and refresh URL patterns."""
    if admin_site.is_registered(Article):
        admin_site.unregister(Article)
    admin_site.register(Article, ArticleAdmin)
    _refresh_urls()


def _refresh_urls():
    """Force Django to rebuild URL patterns by reloading the URL conf module."""
    import tests.settings.urls as url_module

    importlib.reload(url_module)
    clear_url_caches()
    set_urlconf(None)


@override_settings(DEBUG=True)
def test_budget_exceeded_raises(client, superuser, articles):
    class StrictAdmin(QueryBudgetMixin, ModelAdmin):
        query_budget = 1  # impossibly low

    _register(StrictAdmin)
    try:
        client.force_login(superuser)
        with pytest.raises(QueryBudgetExceeded) as exc_info:
            client.get("/admin/testapp/article/")
        assert exc_info.value.actual > 1
        assert exc_info.value.budget == 1
        assert len(exc_info.value.queries) > 0
    finally:
        _restore()


@override_settings(DEBUG=True)
def test_budget_not_exceeded_passes(client, superuser, articles):
    class RelaxedAdmin(QueryBudgetMixin, ModelAdmin):
        query_budget = 100  # generous

    _register(RelaxedAdmin)
    try:
        client.force_login(superuser)
        response = client.get("/admin/testapp/article/")
        assert response.status_code == 200
    finally:
        _restore()


@override_settings(DEBUG=False)
def test_budget_skipped_when_not_debug(client, superuser, articles):
    class StrictAdmin(QueryBudgetMixin, ModelAdmin):
        query_budget = 1

    _register(StrictAdmin)
    try:
        client.force_login(superuser)
        # Should not raise even with budget=1 because DEBUG=False
        response = client.get("/admin/testapp/article/")
        assert response.status_code == 200
    finally:
        _restore()


@override_settings(DEBUG=True)
def test_budget_warn_only_logs(client, superuser, articles, caplog):
    class WarnAdmin(QueryBudgetMixin, ModelAdmin):
        query_budget = 1
        query_budget_warn_only = True

    _register(WarnAdmin)
    try:
        client.force_login(superuser)
        response = client.get("/admin/testapp/article/")
        assert response.status_code == 200
        assert "Query budget exceeded" in caplog.text
    finally:
        _restore()


def test_no_budget_set_skips_check(client, superuser, articles):
    class NobudgetAdmin(QueryBudgetMixin, ModelAdmin):
        pass  # query_budget is None

    _register(NobudgetAdmin)
    try:
        client.force_login(superuser)
        response = client.get("/admin/testapp/article/")
        assert response.status_code == 200
    finally:
        _restore()
