import pytest
from django.contrib.admin import site as admin_site
from django.contrib.auth.models import User

from django_admin_boost.testing import (
    check_add_view_loads,
    check_changelist_loads,
    check_filters_work,
    check_search_works,
    create_admin_smoke_tests,
    get_registered_models,
)
from tests.testapp.models import Article, Category


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin", password="password")


def test_get_registered_models_returns_models():
    models = get_registered_models()
    model_classes = [m for m, _ in models]
    assert Article in model_classes
    assert Category in model_classes


@pytest.mark.django_db
def test_check_changelist_loads(client, superuser):
    check_changelist_loads(client, Article, superuser)


@pytest.mark.django_db
def test_check_add_view_loads(client, superuser):
    model_admin = admin_site._registry[Article]
    check_add_view_loads(client, Article, model_admin, superuser)


@pytest.mark.django_db
def test_check_search_works(client, superuser):
    model_admin = admin_site._registry[Article]
    check_search_works(client, Article, model_admin, superuser)


@pytest.mark.django_db
def test_check_filters_work(client, superuser):
    model_admin = admin_site._registry[Article]
    check_filters_work(client, Article, model_admin, superuser)


# Test the convenience function
test_all_admin_views = create_admin_smoke_tests()
