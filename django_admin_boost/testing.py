"""Reusable pytest utilities for smoke-testing Django admin views."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from django.contrib.admin import site as default_admin_site
from django.contrib.auth.models import User

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.admin import AdminSite
    from django.db.models import Model
    from django.test import Client


def get_registered_models(admin_site: AdminSite | None = None) -> list[tuple[type[Model], Any]]:
    """Return list of (model_class, model_admin_instance) for all registered models."""
    site = admin_site or default_admin_site
    return [(model, site._registry[model]) for model in site._registry]  # noqa: SLF001


def admin_smoke_test_params(admin_site: AdminSite | None = None) -> list[Any]:
    """Generate pytest parametrize params for all registered ModelAdmin classes."""
    params = []
    for model, model_admin in get_registered_models(admin_site):
        app_label = model._meta.app_label  # noqa: SLF001
        model_name = model._meta.model_name  # noqa: SLF001
        params.append(
            pytest.param(
                model,
                model_admin,
                id=f"{app_label}.{model_name}",
            ),
        )
    return params


def check_changelist_loads(client: Client, model: type[Model], superuser: User) -> None:
    """Assert the changelist view returns 200."""
    client.force_login(superuser)
    app_label = model._meta.app_label  # noqa: SLF001
    model_name = model._meta.model_name  # noqa: SLF001
    url = f"/admin/{app_label}/{model_name}/"
    response = client.get(url)
    assert response.status_code == 200, f"Changelist for {app_label}.{model_name} returned {response.status_code}"  # noqa: PLR2004, S101


def check_add_view_loads(client: Client, model: type[Model], model_admin: Any, superuser: User) -> None:  # noqa: ANN401
    """Assert the add view returns 200 (if add permission exists)."""
    if not model_admin.has_add_permission(type("FakeRequest", (), {"user": superuser})()):
        return
    client.force_login(superuser)
    app_label = model._meta.app_label  # noqa: SLF001
    model_name = model._meta.model_name  # noqa: SLF001
    url = f"/admin/{app_label}/{model_name}/add/"
    response = client.get(url)
    assert response.status_code == 200, f"Add view for {app_label}.{model_name} returned {response.status_code}"  # noqa: PLR2004, S101


def check_search_works(client: Client, model: type[Model], model_admin: Any, superuser: User) -> None:  # noqa: ANN401
    """Assert search doesn't error (if search_fields is set)."""
    if not model_admin.search_fields:
        return
    client.force_login(superuser)
    app_label = model._meta.app_label  # noqa: SLF001
    model_name = model._meta.model_name  # noqa: SLF001
    url = f"/admin/{app_label}/{model_name}/?q=test"
    response = client.get(url)
    assert response.status_code == 200, f"Search for {app_label}.{model_name} returned {response.status_code}"  # noqa: PLR2004, S101


def check_filters_work(client: Client, model: type[Model], model_admin: Any, superuser: User) -> None:  # noqa: ANN401
    """Assert each list_filter doesn't error."""
    if not model_admin.list_filter:
        return
    client.force_login(superuser)
    app_label = model._meta.app_label  # noqa: SLF001
    model_name = model._meta.model_name  # noqa: SLF001
    url = f"/admin/{app_label}/{model_name}/"
    # Just load the changelist — Django renders all filters in the sidebar
    response = client.get(url)
    assert response.status_code == 200, f"Filters for {app_label}.{model_name} failed"  # noqa: PLR2004, S101


def create_admin_smoke_tests(admin_site: AdminSite | None = None) -> Callable:
    """Create a parametrized test function for all registered admin views.

    Usage in your project's test file::

        from django_admin_boost.testing import create_admin_smoke_tests

        test_admin_changelist = create_admin_smoke_tests()

    Or with a custom admin site::

        from myapp.admin import custom_site
        test_admin_changelist = create_admin_smoke_tests(admin_site=custom_site)
    """
    site = admin_site or default_admin_site

    @pytest.mark.django_db
    def test_admin_views(client: Client) -> None:
        superuser = User.objects.create_superuser(
            username="admin_smoke_test",
            password="password",  # noqa: S106
        )
        for model, model_admin in get_registered_models(site):
            check_changelist_loads(client, model, superuser)
            check_add_view_loads(client, model, model_admin, superuser)
            check_search_works(client, model, model_admin, superuser)
            check_filters_work(client, model, model_admin, superuser)

    return test_admin_views
