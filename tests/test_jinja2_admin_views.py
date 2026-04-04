"""Integration smoke tests: render admin pages via Jinja2 backend."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from tests.testapp.models import Article

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
class Jinja2LoginTest(TestCase):
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

    def test_invalid_login_shows_errors(self):
        response = self.client.post(
            "/admin/login/",
            {"username": "wrong", "password": "wrong"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "errornote" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2DashboardTest(TestCase):
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
        assert "article" in content.lower()

    def test_app_index_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/")
        assert response.status_code == 200

    def test_auth_app_index_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/")
        assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2HeaderTest(TestCase):
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


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2ChangelistTest(TestCase):
    """Test changelist views render via Jinja2."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )
        for i in range(5):
            Article.objects.create(
                title=f"Article {i}",
                status="published" if i % 2 == 0 else "draft",
            )

    def test_changelist_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/article/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Article 0" in content

    def test_changelist_search(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/article/?q=Article+3")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Article 3" in content

    def test_changelist_has_pagination(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/article/")
        assert response.status_code == 200

    def test_user_changelist_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/user/")
        assert response.status_code == 200

    def test_group_changelist_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/group/")
        assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2ChangeFormTest(TestCase):
    """Test add/change form views render via Jinja2."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )
        cls.article = Article.objects.create(title="Test Article", status="draft")

    def test_add_form_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/testapp/article/add/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "csrf" in content.lower() or "csrfmiddlewaretoken" in content

    def test_change_form_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/testapp/article/{self.article.pk}/change/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Article" in content

    def test_user_add_form_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/user/add/")
        assert response.status_code == 200

    def test_user_change_form_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/auth/user/{self.superuser.pk}/change/")
        assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2DeleteTest(TestCase):
    """Test delete confirmation views render via Jinja2."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )
        cls.article = Article.objects.create(title="To Delete", status="draft")

    def test_delete_confirmation_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/testapp/article/{self.article.pk}/delete/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "To Delete" in content


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2HistoryTest(TestCase):
    """Test object history view renders via Jinja2."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )
        cls.article = Article.objects.create(title="History Test", status="draft")

    def test_history_view_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/testapp/article/{self.article.pk}/history/")
        assert response.status_code == 200


@override_settings(TEMPLATES=JINJA2_TEMPLATES)
class Jinja2PasswordChangeTest(TestCase):
    """Test password change view renders via Jinja2."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
        )

    def test_password_change_renders(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/password_change/")
        assert response.status_code == 200
