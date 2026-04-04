"""Integration smoke tests: render admin pages via Jinja2 backend."""

import pytest
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

JINJA2_TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "django_adminx.jinja2_env.environment",
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
class Jinja2AdminLoginTest(TestCase):
    def test_login_page_renders(self):
        response = self.client.get("/admin/login/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "login-form" in content
        assert 'type="submit"' in content

    def test_login_page_has_csrf(self):
        response = self.client.get("/admin/login/")
        content = response.content.decode()
        assert "csrfmiddlewaretoken" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2AdminDashboardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )

    def test_index_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "recent-actions-module" in content
        assert "content-main" in content

    def test_index_shows_app_list(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        content = response.content.decode()
        # Our testapp should be listed
        assert "Articles" in content or "article" in content.lower()

    def test_app_index_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/")
        assert response.status_code == 200

    def test_auth_app_index_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/")
        assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2AdminHeaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )

    def test_header_shows_username(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        content = response.content.decode()
        assert "admin" in content

    def test_header_has_logout_form(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        content = response.content.decode()
        assert "logout-form" in content

    def test_theme_toggle_present(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        content = response.content.decode()
        assert "theme-toggle" in content


@pytest.mark.django_db
@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2LoginFormErrorsTest(TestCase):
    def test_invalid_login_shows_errors(self):
        response = self.client.post(
            "/admin/login/",
            {"username": "wrong", "password": "wrong"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "errornote" in content
