"""Tests for list_only_fields (explicit whitelist mode of ListFieldsMixin)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import resolve

from django_admin_boost import admin
from django_admin_boost.admin import ModelAdmin
from tests.testapp.models import Article


@pytest.fixture
def list_only_changelist_setup(db):
    superuser = User.objects.create_superuser(username="admin", password="password")
    factory = RequestFactory()
    site = admin.AdminSite()

    class TestArticleAdmin(ModelAdmin):
        list_display = ["title", "status", "created_at"]
        list_only_fields = ["id", "title", "status", "created_at"]

    model_admin = TestArticleAdmin(Article, site)
    return superuser, factory, model_admin


def _make_changelist_request(factory, superuser):
    request = factory.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    return request


def test_only_applied_on_changelist(list_only_changelist_setup):
    superuser, factory, model_admin = list_only_changelist_setup
    request = _make_changelist_request(factory, superuser)
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False, "Expected .only() to be applied (deferred_loading mode)"
    assert set(deferred_fields) == {"id", "title", "status", "created_at"}


def test_queryset_still_works(list_only_changelist_setup):
    """Ensure the queryset actually executes without errors."""
    superuser, factory, model_admin = list_only_changelist_setup
    Article.objects.create(title="Hello", status="published")
    request = _make_changelist_request(factory, superuser)
    qs = model_admin.get_queryset(request)
    assert qs.count() == 1
    article = qs.first()
    assert article is not None
    assert article.title == "Hello"


@pytest.fixture
def list_only_change_view_setup(db):
    superuser = User.objects.create_superuser(username="admin", password="password")
    factory = RequestFactory()
    site = admin.AdminSite()

    class TestArticleAdmin(ModelAdmin):
        list_only_fields = ["id", "title"]

    model_admin = TestArticleAdmin(Article, site)
    return superuser, factory, model_admin


def test_only_not_applied_on_change_view(list_only_change_view_setup):
    superuser, factory, model_admin = list_only_change_view_setup
    article = Article.objects.create(title="Test")
    request = factory.get(f"/admin/testapp/article/{article.pk}/change/")
    request.user = superuser
    request.resolver_match = resolve(f"/admin/testapp/article/{article.pk}/change/")
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


def test_only_not_applied_on_add_view(list_only_change_view_setup):
    superuser, factory, model_admin = list_only_change_view_setup
    request = factory.get("/admin/testapp/article/add/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/add/")
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


@pytest.fixture
def opt_out_setup(db):
    superuser = User.objects.create_superuser(username="admin", password="password")
    factory = RequestFactory()
    site = admin.AdminSite()
    return superuser, factory, site


def test_defer_empty_disables_optimization(opt_out_setup):
    superuser, factory, site = opt_out_setup

    class PlainArticleAdmin(ModelAdmin):
        list_defer_fields = []  # opt-out

    model_admin = PlainArticleAdmin(Article, site)
    request = factory.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


def test_only_empty_means_pk_only(opt_out_setup):
    superuser, factory, site = opt_out_setup

    class PkOnlyAdmin(ModelAdmin):
        list_only_fields = []

    model_admin = PkOnlyAdmin(Article, site)
    request = factory.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert set(deferred_fields) == {"id"}


@pytest.fixture
def standalone_setup(db):
    superuser = User.objects.create_superuser(username="admin", password="password")
    factory = RequestFactory()
    site = admin.AdminSite()

    class CustomAdmin(ModelAdmin):
        list_only_fields = ["id", "title", "status"]

    model_admin = CustomAdmin(Article, site)
    return superuser, factory, model_admin


def test_mixin_works_with_plain_modeladmin(standalone_setup):
    superuser, factory, model_admin = standalone_setup
    request = factory.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    qs = model_admin.get_queryset(request)
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert set(deferred_fields) == {"id", "title", "status"}
