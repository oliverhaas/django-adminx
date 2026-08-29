from django.test import RequestFactory

from django_admin_boost.boost.dashboard import (
    ChartWidget,
    RecentActionsWidget,
    TableWidget,
    ValueWidget,
    Widget,
)


def test_widget_has_template_and_htmx_attrs():
    w = Widget()
    assert hasattr(w, "template_name")
    assert hasattr(w, "htmx")
    assert w.htmx is False


def test_widget_get_context_raises():
    import pytest

    w = Widget()
    factory = RequestFactory()
    request = factory.get("/admin/")
    with pytest.raises(NotImplementedError):
        w.get_context(request)


def test_value_widget_context():
    w = ValueWidget(label="Total Users", value=1234, icon="people")
    factory = RequestFactory()
    request = factory.get("/admin/")
    ctx = w.get_context(request)
    assert ctx["label"] == "Total Users"
    assert ctx["value"] == 1234
    assert ctx["icon"] == "people"


def test_value_widget_callable_value():
    w = ValueWidget(label="Count", value=lambda request: 42)
    factory = RequestFactory()
    request = factory.get("/admin/")
    ctx = w.get_context(request)
    assert ctx["value"] == 42


def test_table_widget_context():
    w = TableWidget(
        title="Recent Orders",
        headers=["ID", "Customer", "Total"],
        rows=lambda request: [["1", "Alice", "$100"], ["2", "Bob", "$200"]],
    )
    factory = RequestFactory()
    request = factory.get("/admin/")
    ctx = w.get_context(request)
    assert ctx["title"] == "Recent Orders"
    assert ctx["headers"] == ["ID", "Customer", "Total"]
    assert len(ctx["rows"]) == 2


def test_chart_widget_is_htmx_by_default():
    w = ChartWidget(
        title="Sales",
        chart_type="bar",
        data=lambda request: {"labels": ["Jan"], "datasets": [{"data": [10]}]},
    )
    assert w.htmx is True


def test_chart_widget_context():
    w = ChartWidget(
        title="Sales",
        chart_type="bar",
        data=lambda request: {"labels": ["Jan"], "datasets": [{"data": [10]}]},
    )
    factory = RequestFactory()
    request = factory.get("/admin/")
    ctx = w.get_context(request)
    assert ctx["title"] == "Sales"
    assert ctx["chart_type"] == "bar"
    assert "labels" in ctx["data"]


def test_recent_actions_widget_context(db):
    w = RecentActionsWidget(limit=5)
    factory = RequestFactory()
    request = factory.get("/admin/")
    request.user = type("User", (), {"is_anonymous": True, "pk": None})()
    ctx = w.get_context(request)
    assert "entries" in ctx
    assert ctx["limit"] == 5
