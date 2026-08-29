"""Pytest configuration."""

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from tests.testapp.models import Article, Category


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin", password="password")


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def category(db):
    return Category.objects.create(name="News")


@pytest.fixture
def articles_10(db):
    return [Article.objects.create(title=f"Article {i}", status="published") for i in range(10)]
