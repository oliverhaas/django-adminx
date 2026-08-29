import pytest
from django.contrib.auth.models import User
from django.test import override_settings

from django_admin_boost.admin import ModelAdmin
from django_admin_boost.boost import site as boost_site
from tests.testapp.models import Article, Category

# Register models with the boost admin site for testing
if not boost_site.is_registered(Article):

    class _ArticleAdmin(ModelAdmin):
        list_display = ["title", "category", "status", "is_featured", "priority", "publish_date", "created_at"]
        list_display_links = ["title"]
        list_filter = ["status", "is_featured", "category"]
        search_fields = ["title", "slug", "body"]
        date_hierarchy = "created_at"
        readonly_fields = ["created_at"]
        fieldsets = [
            (None, {"fields": ["title", "slug", "body", "category"]}),
            ("Publishing", {"fields": ["status", "is_featured", "priority", "publish_date"]}),
            ("Metadata", {"fields": ["created_at"], "classes": ["collapse"]}),
        ]

    class _CategoryAdmin(ModelAdmin):
        list_display = ["name"]
        search_fields = ["name"]

    boost_site.register(Article, _ArticleAdmin)
    boost_site.register(Category, _CategoryAdmin)

BOOST_SETTINGS = {
    "ROOT_URLCONF": "tests.settings.boost_urls",
    "TEMPLATES": [
        {
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "environment": "django_admin_boost.boost.jinja2_env.environment",
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
    ],
}


@pytest.fixture
def boost_setup(db):
    admin_user = User.objects.create_superuser("admin", "admin@test.com", "password")
    category = Category.objects.create(name="Tech")
    article = Article.objects.create(
        title="Test Article",
        slug="test-article",
        body="Test body",
        category=category,
        status=Article.Status.PUBLISHED,
    )
    return admin_user, category, article


@override_settings(**BOOST_SETTINGS)
def test_boost_index(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get("/admin/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_app_index(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get("/admin/testapp/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_change_list(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get("/admin/testapp/article/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_add_form(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get("/admin/testapp/article/add/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_change_form(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get(f"/admin/testapp/article/{article.pk}/change/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_delete_confirmation(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get(f"/admin/testapp/article/{article.pk}/delete/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_object_history(client, boost_setup):
    admin_user, category, article = boost_setup
    client.force_login(admin_user)
    response = client.get(f"/admin/testapp/article/{article.pk}/history/")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_login_page(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200


@pytest.fixture
def boost_search_filter_setup(db):
    admin_user = User.objects.create_superuser("admin", "admin@test.com", "password")
    for i in range(25):
        Article.objects.create(
            title=f"Article {i}",
            status=Article.Status.PUBLISHED if i % 2 else Article.Status.DRAFT,
        )
    return admin_user


@override_settings(**BOOST_SETTINGS)
def test_boost_search(client, boost_search_filter_setup):
    admin_user = boost_search_filter_setup
    client.force_login(admin_user)
    response = client.get("/admin/testapp/article/?q=Article+1")
    assert response.status_code == 200


@override_settings(**BOOST_SETTINGS)
def test_boost_filter(client, boost_search_filter_setup):
    admin_user = boost_search_filter_setup
    client.force_login(admin_user)
    response = client.get("/admin/testapp/article/?status__exact=published")
    assert response.status_code == 200
