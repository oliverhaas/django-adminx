"""Tests for the ListFieldsMixin (list_only_fields, list_defer_fields, auto mode)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import resolve

from django_admin_boost import admin
from django_admin_boost.admin import ModelAdmin
from django_admin_boost.mixins import ListFieldsMixin
from tests.testapp.models import Article


@pytest.fixture
def changelist_base(db):
    superuser = User.objects.create_superuser(username="admin", password="password")
    factory = RequestFactory()
    site = admin.AdminSite()
    return superuser, factory, site


def _changelist_request(factory, superuser):
    request = factory.get("/admin/testapp/article/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/article/")
    return request


def _change_request(factory, superuser, pk=1):
    request = factory.get(f"/admin/testapp/article/{pk}/change/")
    request.user = superuser
    request.resolver_match = resolve(f"/admin/testapp/article/{pk}/change/")
    return request


# --- list_only_fields ---


def test_only_applied_on_changelist(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = ["title", "status"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert "id" in deferred_fields, "pk must always be included"
    assert set(deferred_fields) == {"id", "title", "status"}


def test_pk_auto_included(changelist_base):
    """Even if the user doesn't list pk, it's included."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = ["title"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert "id" in deferred_fields


def test_empty_list_means_pk_only(changelist_base):
    """list_only_fields = [] means .only(pk)."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = []

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert set(deferred_fields) == {"id"}


def test_list_only_not_applied_on_change_view(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = ["title"]

    article = Article.objects.create(title="Test")
    ma = Admin(Article, site)
    qs = ma.get_queryset(_change_request(factory, superuser, article.pk))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


# --- list_defer_fields ---


def test_defer_applied_on_changelist(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_defer_fields = ["body", "slug"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert set(deferred_fields) == {"body", "slug"}


def test_defer_empty_list_means_no_optimization(changelist_base):
    """list_defer_fields = [] is the opt-out escape hatch."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_defer_fields = []

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


def test_defer_not_applied_on_change_view(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_defer_fields = ["body"]

    article = Article.objects.create(title="Test")
    ma = Admin(Article, site)
    qs = ma.get_queryset(_change_request(factory, superuser, article.pk))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


# --- Mutual exclusivity ---


def test_both_set_raises_error(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = ["title"]
        list_defer_fields = ["body"]

    ma = Admin(Article, site)
    with pytest.raises(ImproperlyConfigured, match="Cannot set both"):
        ma.get_queryset(_changelist_request(factory, superuser))


def test_both_set_empty_raises_error(changelist_base):
    """Even two empty lists conflict — the user must pick one."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_only_fields = []
        list_defer_fields = []

    ma = Admin(Article, site)
    with pytest.raises(ImproperlyConfigured, match="Cannot set both"):
        ma.get_queryset(_changelist_request(factory, superuser))


# --- Auto mode ---


def test_auto_resolves_list_display_fields(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["title", "status", "created_at"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert "id" in deferred_fields
    assert set(deferred_fields) == {"id", "title", "status", "created_at"}


def test_auto_includes_pk(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["title"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert "id" in deferred_fields


def test_auto_str_maps_to_pk(changelist_base):
    """__str__ in list_display contributes only pk."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["__str__"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert set(deferred_fields) == {"id"}


def test_auto_skips_callables(changelist_base):
    """Callables/methods that aren't concrete fields are ignored."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["title", "upper_title"]

        def upper_title(self, obj):
            return obj.title.upper()

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    # upper_title is a method, not a field — only title and pk
    assert set(deferred_fields) == {"id", "title"}


def test_auto_not_applied_on_change_view(changelist_base):
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["title"]

    article = Article.objects.create(title="Test")
    ma = Admin(Article, site)
    qs = ma.get_queryset(_change_request(factory, superuser, article.pk))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is True
    assert len(deferred_fields) == 0


def test_auto_handles_fk_field(changelist_base):
    """A ForeignKey in list_display should include the _id column."""
    superuser, factory, site = changelist_base

    class Admin(ModelAdmin):
        list_display = ["title", "category"]

    ma = Admin(Article, site)
    qs = ma.get_queryset(_changelist_request(factory, superuser))
    deferred_fields, is_defer = qs.query.deferred_loading
    assert is_defer is False
    assert "category_id" in deferred_fields or "category" in deferred_fields


# --- Import tests ---


def test_importable_from_mixins():
    assert ListFieldsMixin is not None


def test_importable_from_top_level():
    from django_admin_boost import ListFieldsMixin

    assert ListFieldsMixin is not None


def test_importable_from_admin():
    from django_admin_boost.admin import ListFieldsMixin

    assert ListFieldsMixin is not None
