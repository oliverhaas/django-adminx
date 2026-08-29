import pytest
from django.contrib.admin import site as admin_site
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.test import RequestFactory

from tests.testapp.models import Article, Category


@pytest.fixture
def inline_setup(db):
    category = Category.objects.create(name="News")
    superuser = User.objects.create_superuser(username="admin_inline", password="password")
    return category, superuser


def test_get_form_queryset_is_required(inline_setup):
    from django_admin_boost.admin.contrib.inlines.admin import NonrelatedStackedInline

    category, superuser = inline_setup

    class BadInline(NonrelatedStackedInline):
        model = Category
        fields = ["name"]

    inline = BadInline(Article, admin_site)
    request = RequestFactory().get("/admin/")
    request.user = superuser
    with pytest.raises(NotImplementedError):
        inline.get_formset(request, obj=category)


def test_formset_with_queryset(inline_setup):
    from django_admin_boost.admin.contrib.inlines.admin import NonrelatedStackedInline

    category, superuser = inline_setup

    class CategoryInline(NonrelatedStackedInline):
        model = Category
        fields = ["name"]

        def get_form_queryset(self, obj) -> QuerySet:
            return Category.objects.filter(pk=obj.pk)

        def save_new_instance(self, parent, instance) -> None:
            instance.save()

    inline = CategoryInline(Article, admin_site)
    request = RequestFactory().get("/admin/")
    request.user = superuser
    formset_cls = inline.get_formset(request, obj=category)
    assert formset_cls.provided_queryset.count() == 1


def test_skips_relation_check():
    from django_admin_boost.admin.contrib.inlines.checks import NonrelatedModelAdminChecks

    checker = NonrelatedModelAdminChecks()
    assert checker._check_relation(None, None) == []  # noqa: SLF001


def test_skips_exclude_of_parent_model_check():
    from django_admin_boost.admin.contrib.inlines.checks import NonrelatedModelAdminChecks

    checker = NonrelatedModelAdminChecks()
    assert checker._check_exclude_of_parent_model(None, None) == []  # noqa: SLF001


def test_nonrelated_inline_formset_default_prefix():
    from django_admin_boost.admin.contrib.inlines.forms import (
        nonrelated_inline_formset_factory,
    )

    formset_cls = nonrelated_inline_formset_factory(
        Category,
        queryset=Category.objects.none(),
        save_new_instance=lambda p, i: None,
        fields=["name"],
    )
    assert formset_cls.get_default_prefix() == "testapp-category"
