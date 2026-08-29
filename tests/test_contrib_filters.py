import datetime

import pytest
from django.contrib.admin import site as admin_site
from django.contrib.admin.widgets import AdminRadioSelect, AdminSplitDateTime
from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple, Select
from django.test import RequestFactory, override_settings

from tests.testapp.models import Article


def test_parse_date_str_iso_format():
    from django_admin_boost.admin.contrib.filters.utils import parse_date_str

    result = parse_date_str("2026-01-15")
    assert result == datetime.date(2026, 1, 15)


def test_parse_date_str_returns_none_for_invalid():
    from django_admin_boost.admin.contrib.filters.utils import parse_date_str

    result = parse_date_str("not-a-date")
    assert result is None


@override_settings(DATE_INPUT_FORMATS=["%d/%m/%Y", "%Y-%m-%d"])
def test_parse_date_str_uses_settings_formats():
    from django_admin_boost.admin.contrib.filters.utils import parse_date_str

    result = parse_date_str("15/01/2026")
    assert result == datetime.date(2026, 1, 15)


def test_parse_datetime_str_iso_format():
    from django_admin_boost.admin.contrib.filters.utils import parse_datetime_str

    result = parse_datetime_str("2026-01-15 10:30:00")
    assert result == datetime.datetime(2026, 1, 15, 10, 30, 0)  # noqa: DTZ001


def test_parse_datetime_str_returns_none_for_invalid():
    from django_admin_boost.admin.contrib.filters.utils import parse_datetime_str

    result = parse_datetime_str("not-a-datetime")
    assert result is None


def test_search_form_creates_text_field():
    from django_admin_boost.admin.contrib.filters.forms import SearchForm

    form = SearchForm(name="q", label="Search", data={"q": "test"})
    assert "q" in form.fields
    assert form.fields["q"].required is False


def test_checkbox_form_creates_multiple_choice_field():
    from django_admin_boost.admin.contrib.filters.forms import CheckboxForm

    form = CheckboxForm(
        name="status",
        label="By status",
        choices=[("draft", "Draft"), ("published", "Published")],
        data={"status": ["draft"]},
    )
    assert "status" in form.fields
    assert isinstance(form.fields["status"].widget, CheckboxSelectMultiple)


def test_radio_form_creates_choice_field():
    from django_admin_boost.admin.contrib.filters.forms import RadioForm

    form = RadioForm(
        name="status",
        label="By status",
        choices=[("", "All"), ("draft", "Draft")],
        data={"status": ""},
    )
    assert "status" in form.fields
    assert isinstance(form.fields["status"].widget, AdminRadioSelect)


def test_dropdown_form_creates_select_field():
    from django_admin_boost.admin.contrib.filters.forms import DropdownForm

    form = DropdownForm(
        name="category",
        label="By category",
        choices=[("", "All"), ("1", "News")],
        data={"category": ""},
    )
    assert "category" in form.fields
    assert isinstance(form.fields["category"].widget, Select)


def test_range_numeric_form_creates_from_and_to_fields():
    from django_admin_boost.admin.contrib.filters.forms import RangeNumericForm

    form = RangeNumericForm(name="price", data={})
    assert "price_from" in form.fields
    assert "price_to" in form.fields


def test_single_numeric_form_creates_numeric_field():
    from django_admin_boost.admin.contrib.filters.forms import SingleNumericForm

    form = SingleNumericForm(name="priority", data={})
    assert "priority" in form.fields


def test_range_date_form_creates_date_from_and_to():
    from django_admin_boost.admin.contrib.filters.forms import RangeDateForm

    form = RangeDateForm(name="publish_date", data={})
    assert "publish_date_from" in form.fields
    assert "publish_date_to" in form.fields


def test_range_datetime_form_creates_datetime_from_and_to():
    from django_admin_boost.admin.contrib.filters.forms import RangeDateTimeForm

    form = RangeDateTimeForm(name="created_at", data={})
    assert "created_at_from" in form.fields
    assert "created_at_to" in form.fields
    assert isinstance(form.fields["created_at_from"].widget, AdminSplitDateTime)


def test_value_mixin_returns_first_item_from_list():
    from django_admin_boost.admin.contrib.filters.admin.mixins import ValueMixin

    obj = ValueMixin()
    obj.lookup_val = ["foo", "bar"]
    assert obj.value() == "foo"


def test_value_mixin_returns_none_when_no_value():
    from django_admin_boost.admin.contrib.filters.admin.mixins import ValueMixin

    obj = ValueMixin()
    obj.lookup_val = None
    assert obj.value() is None


def test_multi_value_mixin_returns_list():
    from django_admin_boost.admin.contrib.filters.admin.mixins import MultiValueMixin

    obj = MultiValueMixin()
    obj.lookup_val = ["foo", "bar"]
    assert obj.value() == ["foo", "bar"]


@pytest.mark.django_db
def test_range_numeric_mixin_filters_queryset_by_range():
    from django_admin_boost.admin.contrib.filters.admin.mixins import RangeNumericMixin

    Article.objects.create(title="Cheap", priority=10)
    Article.objects.create(title="Expensive", priority=90)

    mixin = RangeNumericMixin.__new__(RangeNumericMixin)
    mixin.parameter_name = "priority"
    mixin.used_parameters = {"priority_from": "10", "priority_to": "50"}
    qs = Article.objects.all()
    result = mixin.queryset(None, qs)
    assert result.count() == 1
    assert result.first().title == "Cheap"


def test_range_numeric_mixin_expected_parameters():
    from django_admin_boost.admin.contrib.filters.admin.mixins import RangeNumericMixin

    mixin = RangeNumericMixin.__new__(RangeNumericMixin)
    mixin.parameter_name = "priority"
    assert mixin.expected_parameters() == ["priority_from", "priority_to"]


def test_text_filter_has_output_returns_true():
    from django_admin_boost.admin.contrib.filters.admin.text_filters import TextFilter

    class TitleFilter(TextFilter):
        title = "Title"
        parameter_name = "title__icontains"

        def lookups(self, request, model_admin):
            return ()

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(title__icontains=self.value())
            return queryset

    f = TitleFilter(None, {}, Article, None)
    assert f.has_output() is True


@pytest.fixture
def field_text_filter_articles(db):
    Article.objects.create(title="Hello World")
    Article.objects.create(title="Goodbye World")
    return User.objects.create_superuser(username="admin_text", password="password")


def test_field_text_filter_filters_by_icontains(field_text_filter_articles):
    from django_admin_boost.admin import ModelAdmin
    from django_admin_boost.admin.contrib.filters.admin.text_filters import FieldTextFilter

    superuser = field_text_filter_articles

    class ArticleAdmin(ModelAdmin):
        list_filter = [("title", FieldTextFilter)]

    ma = ArticleAdmin(Article, admin_site)
    request = RequestFactory().get(
        "/admin/testapp/article/",
        {"title__icontains": "Hello"},
    )
    request.user = superuser
    changelist = ma.get_changelist_instance(request)
    qs = changelist.get_queryset(request)
    assert qs.count() == 1
    assert qs.first().title == "Hello World"


@pytest.fixture
def range_numeric_articles(db):
    Article.objects.create(title="Low", priority=5)
    Article.objects.create(title="Mid", priority=50)
    Article.objects.create(title="High", priority=95)
    return User.objects.create_superuser(username="admin_numeric", password="password")


def test_range_numeric_filter_filters_by_range(range_numeric_articles):
    from django_admin_boost.admin import ModelAdmin
    from django_admin_boost.admin.contrib.filters.admin.numeric_filters import (
        RangeNumericFilter,
    )

    superuser = range_numeric_articles

    class ArticleAdmin(ModelAdmin):
        list_filter = [("priority", RangeNumericFilter)]

    ma = ArticleAdmin(Article, admin_site)
    request = RequestFactory().get(
        "/admin/testapp/article/",
        {"priority_from": "10", "priority_to": "60"},
    )
    request.user = superuser
    changelist = ma.get_changelist_instance(request)
    qs = changelist.get_queryset(request)
    assert qs.count() == 1
    assert qs.first().title == "Mid"


@pytest.fixture
def single_numeric_articles(db):
    Article.objects.create(title="Target", priority=42)
    Article.objects.create(title="Other", priority=99)
    return User.objects.create_superuser(username="admin_single", password="password")


def test_single_numeric_filter_filters_exact(single_numeric_articles):
    from django_admin_boost.admin import ModelAdmin
    from django_admin_boost.admin.contrib.filters.admin.numeric_filters import (
        SingleNumericFilter,
    )

    superuser = single_numeric_articles

    class ArticleAdmin(ModelAdmin):
        list_filter = [("priority", SingleNumericFilter)]

    ma = ArticleAdmin(Article, admin_site)
    request = RequestFactory().get("/admin/testapp/article/", {"priority": "42"})
    request.user = superuser
    changelist = ma.get_changelist_instance(request)
    qs = changelist.get_queryset(request)
    assert qs.count() == 1
    assert qs.first().title == "Target"


@pytest.fixture
def range_date_articles(db):
    Article.objects.create(title="Old", publish_date=datetime.date(2025, 1, 1))
    Article.objects.create(title="Recent", publish_date=datetime.date(2026, 3, 15))
    Article.objects.create(title="Future", publish_date=datetime.date(2027, 6, 1))
    return User.objects.create_superuser(username="admin_date", password="password")


def test_range_date_filter_filters_by_date_range(range_date_articles):
    from django_admin_boost.admin import ModelAdmin
    from django_admin_boost.admin.contrib.filters.admin.datetime_filters import (
        RangeDateFilter,
    )

    superuser = range_date_articles

    class ArticleAdmin(ModelAdmin):
        list_filter = [("publish_date", RangeDateFilter)]

    ma = ArticleAdmin(Article, admin_site)
    request = RequestFactory().get(
        "/admin/testapp/article/",
        {"publish_date_from": "2026-01-01", "publish_date_to": "2026-12-31"},
    )
    request.user = superuser
    changelist = ma.get_changelist_instance(request)
    qs = changelist.get_queryset(request)
    assert qs.count() == 1
    assert qs.first().title == "Recent"


def test_all_filters_importable():
    from django_admin_boost.admin.contrib.filters.admin import (
        AutocompleteSelectFilter,
        AutocompleteSelectMultipleFilter,
        BooleanRadioFilter,
        DropdownFilter,
        FieldTextFilter,
        RadioFilter,
        RangeDateFilter,
        RangeDateTimeFilter,
        RangeNumericFilter,
        SingleNumericFilter,
        SliderNumericFilter,
        TextFilter,
    )

    assert all(
        [
            TextFilter,
            FieldTextFilter,
            RadioFilter,
            BooleanRadioFilter,
            RangeDateFilter,
            RangeDateTimeFilter,
            SingleNumericFilter,
            RangeNumericFilter,
            SliderNumericFilter,
            DropdownFilter,
            AutocompleteSelectFilter,
            AutocompleteSelectMultipleFilter,
        ],
    )
