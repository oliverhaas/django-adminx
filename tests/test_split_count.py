import pytest
from django.db.models import Count

from django_admin_boost.paginators import EstimatedCountPaginator
from tests.testapp.models import Article, Category


@pytest.fixture
def articles_with_categories(db):
    cat = Category.objects.create(name="News")
    for i in range(10):
        Article.objects.create(title=f"Article {i}", category=cat)
    return cat


def test_count_strips_display_annotations(articles_with_categories):
    """Display-only annotations should be stripped from count query."""
    qs = Category.objects.annotate(article_count=Count("article"))
    paginator = EstimatedCountPaginator(qs, per_page=10)
    # Count should work and return 1
    assert paginator.count == 1


def test_count_preserves_filter_annotations(db):
    """Annotations used in filters should be preserved."""
    Category.objects.create(name="Empty")
    cat = Category.objects.create(name="Has articles")
    Article.objects.create(title="A1", category=cat)

    qs = Category.objects.annotate(
        article_count=Count("article"),
    ).filter(article_count__gt=0)

    paginator = EstimatedCountPaginator(qs, per_page=10)
    assert paginator.count == 1


def test_count_no_annotations_unchanged(db):
    """Queryset without annotations should count normally."""
    for i in range(5):
        Article.objects.create(title=f"Article {i}")

    qs = Article.objects.all()
    paginator = EstimatedCountPaginator(qs, per_page=10)
    assert paginator.count == 5


def test_count_preserves_ordering_annotations(db):
    """Annotations used in ordering should be preserved."""
    cat = Category.objects.create(name="News")
    Article.objects.create(title="A1", category=cat)

    qs = Category.objects.annotate(
        article_count=Count("article"),
    ).order_by("-article_count")

    paginator = EstimatedCountPaginator(qs, per_page=10)
    assert paginator.count == 1
