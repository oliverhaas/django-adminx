"""Render-parity tests: verify django-adminx output matches django.contrib.admin.

Each test renders an admin view twice — once via our Jinja2 templates,
once via Django's *original* DTL templates (from the django package) —
then compares the normalized HTML. Differences indicate conversion bugs.
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from tests.testapp.models import Article

# Path to Django's original admin templates (the baseline we compare against)
_DJANGO_ADMIN_TEMPLATES = str(
    Path(__import__("django.contrib.admin", fromlist=["admin"]).__file__).parent / "templates",
)

# --- Template backend configurations ---

# Our Jinja2 templates (what we're testing)
JINJA2_ADMINX = [
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

# Django's original DTL templates (the baseline).
# DIRS is listed before APP_DIRS, so Django's originals win over ours.
DJANGO_ORIGINAL_DTL = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [_DJANGO_ADMIN_TEMPLATES],
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


# --- HTML normalization ---


def normalize_html(html: str) -> BeautifulSoup:
    """Parse HTML and return a normalized BeautifulSoup tree.

    Strips dynamic content that legitimately differs between renders
    (CSRF tokens, timestamps, etc.) so we can compare structure and text.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove CSRF tokens (different per request)
    for inp in soup.find_all("input", {"name": "csrfmiddlewaretoken"}):
        inp.decompose()

    # Remove data-admin-utc-offset (contains current time)
    for tag in soup.find_all(attrs={"data-admin-utc-offset": True}):
        del tag["data-admin-utc-offset"]

    # Remove all script tags with nonce attributes
    for script in soup.find_all("script", {"nonce": True}):
        del script["nonce"]

    return soup


def extract_text_content(soup: BeautifulSoup) -> str:
    """Extract visible text from the parsed HTML, normalized."""
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Normalize unicode quotes/apostrophes to ASCII equivalents
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # curly double quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")  # curly single quotes
    text = text.replace("\u2013", "-").replace("\u2014", "-")  # en/em dashes
    text = text.replace("\xa0", " ")  # non-breaking space
    return text


def extract_structure(soup: BeautifulSoup) -> list[str]:
    """Extract the tag structure (tag names + key attributes) for comparison."""
    structure = []
    for tag in soup.find_all(True):
        attrs = []
        if tag.get("id"):
            attrs.append(f'id="{tag["id"]}"')
        if tag.get("class"):
            attrs.append(f'class="{" ".join(tag["class"])}"')
        if tag.get("name") and tag.name in ("input", "select", "textarea"):
            attrs.append(f'name="{tag["name"]}"')
        attr_str = " ".join(attrs)
        structure.append(f"<{tag.name} {attr_str}>" if attr_str else f"<{tag.name}>")
    return structure


def compare_renders(jinja2_html: str, dtl_html: str) -> list[str]:
    """Compare two rendered HTML strings and return a list of differences."""
    j_soup = normalize_html(jinja2_html)
    d_soup = normalize_html(dtl_html)

    diffs = []

    # Compare text content
    j_text = extract_text_content(j_soup)
    d_text = extract_text_content(d_soup)
    if j_text != d_text:
        # Find the first divergence point
        j_words = j_text.split()
        d_words = d_text.split()
        for i, (jw, dw) in enumerate(zip(j_words, d_words)):
            if jw != dw:
                context_start = max(0, i - 3)
                j_context = " ".join(j_words[context_start : i + 5])
                d_context = " ".join(d_words[context_start : i + 5])
                diffs.append(f"Text differs at word {i}: Jinja2='...{j_context}...' vs DTL='...{d_context}...'")
                break
        if len(j_words) != len(d_words):
            diffs.append(f"Text length differs: Jinja2={len(j_words)} words vs DTL={len(d_words)} words")

    # Compare structure (tag count by type)
    j_tags = {}
    for tag in j_soup.find_all(True):
        j_tags[tag.name] = j_tags.get(tag.name, 0) + 1
    d_tags = {}
    for tag in d_soup.find_all(True):
        d_tags[tag.name] = d_tags.get(tag.name, 0) + 1

    all_tag_names = set(j_tags) | set(d_tags)
    for tag_name in sorted(all_tag_names):
        j_count = j_tags.get(tag_name, 0)
        d_count = d_tags.get(tag_name, 0)
        if j_count != d_count:
            diffs.append(f"Tag <{tag_name}> count: Jinja2={j_count} vs DTL={d_count}")

    # Compare IDs present
    j_ids = {tag["id"] for tag in j_soup.find_all(id=True)}
    d_ids = {tag["id"] for tag in d_soup.find_all(id=True)}
    missing_ids = d_ids - j_ids
    extra_ids = j_ids - d_ids
    if missing_ids:
        diffs.append(f"IDs missing in Jinja2: {missing_ids}")
    if extra_ids:
        diffs.append(f"IDs extra in Jinja2: {extra_ids}")

    # Compare form inputs (name attributes)
    j_inputs = {inp.get("name") for inp in j_soup.find_all(["input", "select", "textarea"]) if inp.get("name")}
    d_inputs = {inp.get("name") for inp in d_soup.find_all(["input", "select", "textarea"]) if inp.get("name")}
    missing_inputs = d_inputs - j_inputs
    extra_inputs = j_inputs - d_inputs
    if missing_inputs:
        diffs.append(f"Form inputs missing in Jinja2: {missing_inputs}")
    if extra_inputs:
        diffs.append(f"Form inputs extra in Jinja2: {extra_inputs}")

    return diffs


# --- Test helpers ---


class RenderParityMixin:
    """Mixin that provides render_both() to get Jinja2 and DTL output for the same URL."""

    def render_both(self, path: str) -> tuple[str, str]:
        """Render a URL with our Jinja2 and Django's original DTL, return both."""
        with override_settings(TEMPLATES=JINJA2_ADMINX):
            j_response = self.client.get(path)  # type: ignore[attr-defined]
            assert j_response.status_code == 200, f"Jinja2 render failed for {path}: {j_response.status_code}"
            j_html = j_response.content.decode()

        with override_settings(TEMPLATES=DJANGO_ORIGINAL_DTL):
            d_response = self.client.get(path)  # type: ignore[attr-defined]
            assert d_response.status_code == 200, f"Django DTL render failed for {path}: {d_response.status_code}"
            d_html = d_response.content.decode()

        return j_html, d_html

    def assert_parity(self, path: str, *, allow_diffs: list[str] | None = None) -> None:
        """Assert that Jinja2 and DTL renders match for the given URL."""
        j_html, d_html = self.render_both(path)
        diffs = compare_renders(j_html, d_html)

        # Filter out known/allowed differences
        if allow_diffs:
            diffs = [d for d in diffs if not any(allowed in d for allowed in allow_diffs)]

        if diffs:
            msg = f"Render parity failed for {path}:\n" + "\n".join(f"  - {d}" for d in diffs)
            raise AssertionError(msg)


# --- Tests ---


class LoginParityTest(RenderParityMixin, TestCase):
    def test_login_page(self):
        self.assert_parity("/admin/login/")


class DashboardParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_index(self):
        self.assert_parity("/admin/")

    def test_app_index(self):
        self.assert_parity("/admin/testapp/")

    def test_auth_app_index(self):
        self.assert_parity("/admin/auth/")


class ChangelistParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")
        for i in range(5):
            Article.objects.create(title=f"Article {i}", status="published" if i % 2 == 0 else "draft")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist(self):
        self.assert_parity("/admin/testapp/article/")

    def test_changelist_search(self):
        self.assert_parity("/admin/testapp/article/?q=Article")


class ChangeFormParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")
        cls.article = Article.objects.create(title="Parity Test", status="draft")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_add_form(self):
        self.assert_parity("/admin/testapp/article/add/")

    def test_change_form(self):
        self.assert_parity(f"/admin/testapp/article/{self.article.pk}/change/")


class DeleteParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")
        cls.article = Article.objects.create(title="Delete Me", status="draft")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_delete_confirmation(self):
        self.assert_parity(f"/admin/testapp/article/{self.article.pk}/delete/")


class HistoryParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")
        cls.article = Article.objects.create(title="History Test", status="draft")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_history(self):
        self.assert_parity(f"/admin/testapp/article/{self.article.pk}/history/")


class PasswordChangeParityTest(RenderParityMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="password")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_password_change(self):
        self.assert_parity("/admin/password_change/")
