from django.contrib.admin.exceptions import AlreadyRegistered as _DjangoAlreadyRegistered
from django.contrib.admin.exceptions import NotRegistered as _DjangoNotRegistered
from django.core.exceptions import SuspiciousOperation


class DisallowedModelAdminLookup(SuspiciousOperation):
    """Invalid filter was passed to admin view via URL querystring"""


class DisallowedModelAdminToField(SuspiciousOperation):
    """Invalid to_field was passed to admin view via URL query string"""


class AlreadyRegistered(_DjangoAlreadyRegistered):
    """The model is already registered."""


class NotRegistered(_DjangoNotRegistered):
    """The model is not registered."""
