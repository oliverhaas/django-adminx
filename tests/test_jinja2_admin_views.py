"""Integration smoke tests: render admin pages via Jinja2 backend."""

import pytest
from django.contrib.auth.models import User
from django.test import override_settings

from tests.testapp.models import Article

JINJA2_TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "django_admin_boost.admin.jinja2_env.environment",
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_login_page_renders(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "login-form" in content
    assert 'type="submit"' in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_login_page_has_csrf(client):
    response = client.get("/admin/login/")
    content = response.content.decode()
    assert "csrfmiddlewaretoken" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_invalid_login_shows_errors(client, db):
    response = client.post(
        "/admin/login/",
        {"username": "wrong", "password": "wrong"},
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "errornote" in content


@pytest.fixture
def jinja2_superuser(db):
    return User.objects.create_superuser(username="admin", password="password")


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_index_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "recent-actions-module" in content
    assert "content-main" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_index_shows_app_list(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/")
    content = response.content.decode()
    assert "article" in content.lower()


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_app_index_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/testapp/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_auth_app_index_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/auth/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_header_shows_username(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/")
    content = response.content.decode()
    assert "admin" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_header_has_logout_form(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/")
    content = response.content.decode()
    assert "logout-form" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_theme_toggle_present(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/")
    content = response.content.decode()
    assert "theme-toggle" in content


@pytest.fixture
def jinja2_articles(db):
    return [
        Article.objects.create(
            title=f"Article {i}",
            status="published" if i % 2 == 0 else "draft",
        )
        for i in range(5)
    ]


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_changelist_renders(client, jinja2_superuser, jinja2_articles):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/testapp/article/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Article 0" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_changelist_search(client, jinja2_superuser, jinja2_articles):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/testapp/article/?q=Article+3")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Article 3" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_changelist_has_pagination(client, jinja2_superuser, jinja2_articles):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/testapp/article/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_user_changelist_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/auth/user/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_group_changelist_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/auth/group/")
    assert response.status_code == 200


@pytest.fixture
def jinja2_article(db):
    return Article.objects.create(title="Test Article", status="draft")


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_add_form_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/testapp/article/add/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "csrf" in content.lower() or "csrfmiddlewaretoken" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_change_form_renders(client, jinja2_superuser, jinja2_article):
    client.force_login(jinja2_superuser)
    response = client.get(f"/admin/testapp/article/{jinja2_article.pk}/change/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Test Article" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_user_add_form_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/auth/user/add/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_user_change_form_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get(f"/admin/auth/user/{jinja2_superuser.pk}/change/")
    assert response.status_code == 200


@pytest.fixture
def article_to_delete(db):
    return Article.objects.create(title="To Delete", status="draft")


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_delete_confirmation_renders(client, jinja2_superuser, article_to_delete):
    client.force_login(jinja2_superuser)
    response = client.get(f"/admin/testapp/article/{article_to_delete.pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "To Delete" in content


@pytest.fixture
def article_for_history(db):
    return Article.objects.create(title="History Test", status="draft")


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_history_view_renders(client, jinja2_superuser, article_for_history):
    client.force_login(jinja2_superuser)
    response = client.get(f"/admin/testapp/article/{article_for_history.pk}/history/")
    assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
def test_password_change_renders(client, jinja2_superuser):
    client.force_login(jinja2_superuser)
    response = client.get("/admin/password_change/")
    assert response.status_code == 200
