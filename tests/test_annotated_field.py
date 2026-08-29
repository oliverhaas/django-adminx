import pytest
from django.contrib.admin import site as admin_site
from django.db.models import Count
from django.test import RequestFactory
from django.urls import resolve

from django_admin_boost.admin import ModelAdmin
from django_admin_boost.annotations import AnnotatedField
from tests.testapp.models import Article, Category


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


def test_annotated_field_applies_annotation(rf, superuser, db):
    class TestAdmin(ModelAdmin):
        list_display = ["name", AnnotatedField("article_count", Count("article"))]

    ma = TestAdmin(Category, admin_site)
    request = rf.get("/admin/testapp/category/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/category/")
    qs = ma.get_queryset(request)
    assert "article_count" in qs.query.annotations


def test_annotated_field_callable(db):
    af = AnnotatedField("tag_count", Count("tags"), short_description="Tags")

    class FakeObj:
        tag_count = 5

    assert af(FakeObj()) == 5
    assert af.short_description == "Tags"
    assert af.admin_order_field == "tag_count"


def test_annotated_field_empty_value(db):
    af = AnnotatedField("tag_count", Count("tags"), empty_value="N/A")

    class FakeObj:
        tag_count = None

    assert af(FakeObj()) == "N/A"


def test_annotated_field_default_description():
    af = AnnotatedField("article_count", Count("article"))
    assert af.short_description == "Article Count"


def test_annotated_field_queryset_value(rf, superuser, db):
    cat = Category.objects.create(name="News")
    Article.objects.create(title="A1", category=cat)
    Article.objects.create(title="A2", category=cat)

    class TestAdmin(ModelAdmin):
        list_display = ["name", AnnotatedField("article_count", Count("article"))]

    ma = TestAdmin(Category, admin_site)
    request = rf.get("/admin/testapp/category/")
    request.user = superuser
    request.resolver_match = resolve("/admin/testapp/category/")
    qs = ma.get_queryset(request)
    obj = qs.get(pk=cat.pk)
    assert obj.article_count == 2


def test_only_fields_skips_annotated_field(rf, superuser, db):
    """AnnotatedField should not appear in _resolve_list_display_fields."""

    class TestAdmin(ModelAdmin):
        list_display = ["name", AnnotatedField("article_count", Count("article"))]

    ma = TestAdmin(Category, admin_site)
    fields = ma._resolve_list_display_fields()  # noqa: SLF001
    assert "article_count" not in fields
