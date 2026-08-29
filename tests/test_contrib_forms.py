def test_array_widget_decompress_list():
    from django_admin_boost.admin.contrib.forms.widgets import ArrayWidget

    widget = ArrayWidget()
    assert widget.decompress(["a", "b"]) == ["a", "b"]


def test_array_widget_decompress_csv_string():
    from django_admin_boost.admin.contrib.forms.widgets import ArrayWidget

    widget = ArrayWidget()
    assert widget.decompress("a,b,c") == ["a", "b", "c"]


def test_array_widget_decompress_none():
    from django_admin_boost.admin.contrib.forms.widgets import ArrayWidget

    widget = ArrayWidget()
    assert widget.decompress(None) == []


def test_array_widget_value_from_datadict_filters_empty():
    from django.http import QueryDict

    from django_admin_boost.admin.contrib.forms.widgets import ArrayWidget

    widget = ArrayWidget()
    data = QueryDict(mutable=True)
    data.setlist("tags", ["foo", "", "bar"])
    result = widget.value_from_datadict(data, {}, "tags")
    assert result == ["foo", "bar"]


def test_array_widget_custom_widget_class():
    from django.forms import NumberInput

    from django_admin_boost.admin.contrib.forms.widgets import ArrayWidget

    widget = ArrayWidget(widget_class=NumberInput)
    instance = widget.get_widget_instance()
    assert isinstance(instance, NumberInput)


def test_wysiwyg_widget_template_name():
    from django_admin_boost.admin.contrib.forms.widgets import WysiwygWidget

    widget = WysiwygWidget()
    assert widget.template_name == "admin/forms/wysiwyg.html"


def test_wysiwyg_widget_media_includes_trix():
    from django_admin_boost.admin.contrib.forms.widgets import WysiwygWidget

    widget = WysiwygWidget()
    media_str = str(widget.media)
    assert "trix.js" in media_str
    assert "trix.css" in media_str
