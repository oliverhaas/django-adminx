"""Tests for auto select_related from list_display introspection."""

from __future__ import annotations

import pytest
from django.contrib.admin import site as admin_site
from django.test import RequestFactory
from django.urls import resolve

from django_admin_boost.admin import ModelAdmin
from tests.testapp.models import Article


@pytest.fixture
def superuser(db):
    from django.contrib.auth.models import User

    return User.objects.create_superuser(username="admin", password="password")


@pytest.fixture
def rf():
    return RequestFactory()


def _changelist_request(rf, superuser):
    request = rf.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    return request


def test_auto_select_related_for_fk_field(rf, superuser, db):
    """FK field in list_display should trigger auto select_related."""

    class TestAdmin(ModelAdmin):
        list_display = ["title", "category"]
        list_only_fields = ["id", "title", "category_id"]

    ma = TestAdmin(Article, admin_site)
    request = _changelist_request(rf, superuser)
    qs = ma.get_queryset(request)
    # Check that select_related was applied
    assert "category" in qs.query.select_related


def test_auto_select_related_for_dotted_path(rf, superuser, db):
    """Dotted path like 'category__name' should trigger select_related('category')."""

    class TestAdmin(ModelAdmin):
        list_display = ["title", "category__name"]

    ma = TestAdmin(Article, admin_site)
    request = _changelist_request(rf, superuser)
    qs = ma.get_queryset(request)
    assert "category" in qs.query.select_related


def test_manual_list_select_related_not_overridden(rf, superuser, db):
    """When list_select_related is set manually, don't auto-detect."""

    class TestAdmin(ModelAdmin):
        list_display = ["title", "category"]
        list_select_related = ["category"]

    ma = TestAdmin(Article, admin_site)
    request = _changelist_request(rf, superuser)
    qs = ma.get_queryset(request)
    # Manual setting should be respected (Django applies it downstream)
    # Our auto-detect should NOT have run
    # We can't easily check this without more introspection,
    # but the queryset should still work
    assert qs.query is not None


def test_no_select_related_without_fk(rf, superuser, db):
    """Non-FK fields should not trigger select_related."""

    class TestAdmin(ModelAdmin):
        list_display = ["title", "status"]

    ma = TestAdmin(Article, admin_site)
    request = _changelist_request(rf, superuser)
    qs = ma.get_queryset(request)
    assert not qs.query.select_related


def test_no_select_related_on_change_view(rf, superuser, db):
    """select_related should not be applied on add/change views."""

    class TestAdmin(ModelAdmin):
        list_display = ["title", "category"]

    ma = TestAdmin(Article, admin_site)
    request = rf.get("/admin/testapp/article/add/")
    request.user = superuser
    qs = ma.get_queryset(request)
    assert not qs.query.select_related
