"""Render-parity tests: verify django-adminx output matches django.contrib.admin.

Each test renders an admin view three ways:
1. Our Jinja2 templates (the primary product)
2. Our DTL templates (copied from Django, should be identical)
3. Django's original DTL templates (the ground truth baseline)

Then compares (1) vs (3) and (2) vs (3) to catch conversion bugs and
accidental regressions in the DTL copies.
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

# Our DTL copies (APP_DIRS finds django_adminx/templates/admin/)
DTL_ADMINX = [
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

# Django's original DTL templates (the ground truth).
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
    return text.replace("\xa0", " ")  # non-breaking space


def compare_renders(test_html: str, baseline_html: str, label: str = "test") -> list[str]:
    """Compare two rendered HTML strings and return a list of differences."""
    t_soup = normalize_html(test_html)
    b_soup = normalize_html(baseline_html)

    diffs = []

    # Compare text content
    t_text = extract_text_content(t_soup)
    b_text = extract_text_content(b_soup)
    if t_text != b_text:
        t_words = t_text.split()
        b_words = b_text.split()
        for i, (tw, bw) in enumerate(zip(t_words, b_words)):
            if tw != bw:
                context_start = max(0, i - 3)
                t_context = " ".join(t_words[context_start : i + 5])
                b_context = " ".join(b_words[context_start : i + 5])
                diffs.append(f"Text differs at word {i}: {label}='...{t_context}...' vs baseline='...{b_context}...'")
                break
        if len(t_words) != len(b_words):
            diffs.append(f"Text length: {label}={len(t_words)} words vs baseline={len(b_words)} words")

    # Compare tag counts
    t_tags = {}
    for tag in t_soup.find_all(True):
        t_tags[tag.name] = t_tags.get(tag.name, 0) + 1
    b_tags = {}
    for tag in b_soup.find_all(True):
        b_tags[tag.name] = b_tags.get(tag.name, 0) + 1

    for tag_name in sorted(set(t_tags) | set(b_tags)):
        t_count = t_tags.get(tag_name, 0)
        b_count = b_tags.get(tag_name, 0)
        if t_count != b_count:
            diffs.append(f"<{tag_name}> count: {label}={t_count} vs baseline={b_count}")

    # Compare IDs
    t_ids = {tag["id"] for tag in t_soup.find_all(id=True)}
    b_ids = {tag["id"] for tag in b_soup.find_all(id=True)}
    if b_ids - t_ids:
        diffs.append(f"IDs missing in {label}: {b_ids - t_ids}")
    if t_ids - b_ids:
        diffs.append(f"IDs extra in {label}: {t_ids - b_ids}")

    # Compare form inputs
    t_inputs = {inp.get("name") for inp in t_soup.find_all(["input", "select", "textarea"]) if inp.get("name")}
    b_inputs = {inp.get("name") for inp in b_soup.find_all(["input", "select", "textarea"]) if inp.get("name")}
    if b_inputs - t_inputs:
        diffs.append(f"Form inputs missing in {label}: {b_inputs - t_inputs}")
    if t_inputs - b_inputs:
        diffs.append(f"Form inputs extra in {label}: {t_inputs - b_inputs}")

    return diffs


# --- Test helpers ---


def _render_with(client, path: str, templates: list) -> str:
    """Render a URL with the given TEMPLATES setting, return HTML."""
    with override_settings(TEMPLATES=templates):
        response = client.get(path)
        assert response.status_code == 200, f"Render failed for {path}: {response.status_code}"
        return response.content.decode()


class RenderParityMixin:
    """Mixin providing assert_parity() that compares both Jinja2 and DTL against Django's originals."""

    def assert_parity(self, path: str) -> None:
        """Assert that both our Jinja2 AND DTL renders match Django's original."""
        baseline = _render_with(self.client, path, DJANGO_ORIGINAL_DTL)  # type: ignore[attr-defined]
        jinja2_html = _render_with(self.client, path, JINJA2_ADMINX)  # type: ignore[attr-defined]
        dtl_html = _render_with(self.client, path, DTL_ADMINX)  # type: ignore[attr-defined]

        all_diffs = []

        jinja2_diffs = compare_renders(jinja2_html, baseline, label="jinja2")
        if jinja2_diffs:
            all_diffs.append("Jinja2 vs Django original:")
            all_diffs.extend(f"  - {d}" for d in jinja2_diffs)

        dtl_diffs = compare_renders(dtl_html, baseline, label="dtl")
        if dtl_diffs:
            all_diffs.append("DTL copy vs Django original:")
            all_diffs.extend(f"  - {d}" for d in dtl_diffs)

        if all_diffs:
            msg = f"Render parity failed for {path}:\n" + "\n".join(all_diffs)
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
