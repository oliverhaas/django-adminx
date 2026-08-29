import pytest
from django.contrib.admin import site as admin_site
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.test import RequestFactory, TestCase

from tests.testapp.models import Article, Category


class NonrelatedInlineMixinTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = Category.objects.create(name="News")
        cls.superuser = User.objects.create_superuser(
            username="admin_inline",
            password="password",
        )

    def test_get_form_queryset_is_required(self) -> None:
        from django_admin_boost.admin.contrib.inlines.admin import NonrelatedStackedInline

        class BadInline(NonrelatedStackedInline):
            model = Category
            fields = ["name"]

        inline = BadInline(Article, admin_site)
        request = RequestFactory().get("/admin/")
        request.user = self.superuser
        with pytest.raises(NotImplementedError):
            inline.get_formset(request, obj=self.category)

    def test_formset_with_queryset(self) -> None:
        from django_admin_boost.admin.contrib.inlines.admin import NonrelatedStackedInline

        class CategoryInline(NonrelatedStackedInline):
            model = Category
            fields = ["name"]

            def get_form_queryset(self, obj) -> QuerySet:
                return Category.objects.filter(pk=obj.pk)

            def save_new_instance(self, parent, instance) -> None:
                instance.save()

        inline = CategoryInline(Article, admin_site)
        request = RequestFactory().get("/admin/")
        request.user = self.superuser
        formset_cls = inline.get_formset(request, obj=self.category)
        assert formset_cls.provided_queryset.count() == 1


class NonrelatedModelAdminChecksTest(TestCase):
    def test_skips_relation_check(self) -> None:
        from django_admin_boost.admin.contrib.inlines.checks import NonrelatedModelAdminChecks

        checker = NonrelatedModelAdminChecks()
        assert checker._check_relation(None, None) == []

    def test_skips_exclude_of_parent_model_check(self) -> None:
        from django_admin_boost.admin.contrib.inlines.checks import NonrelatedModelAdminChecks

        checker = NonrelatedModelAdminChecks()
        assert checker._check_exclude_of_parent_model(None, None) == []


class NonrelatedInlineFormSetTest(TestCase):
    def test_default_prefix(self) -> None:
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
