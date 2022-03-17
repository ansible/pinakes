"""Test sanitize order item's parameters"""
import pytest

from pinakes.main.catalog.services.sanitize_parameters import (
    SanitizeParameters,
)
from pinakes.main.catalog.tests.factories import ServicePlanFactory
from pinakes.main.catalog.exceptions import BadParamsException


_FIELDS = [
    {
        "name": "Totally not a pass",
        "type": "password",
        "label": "Totally not a pass",
        "component": "text-field",
        "helperText": "",
        "isRequired": True,
        "initialValue": "",
    },
    {
        "name": "most_important_var1",
        "label": "secret field 1",
        "component": "textarea-field",
        "helperText": "Has no effect on anything, ever.",
        "initialValue": "",
    },
    {
        "name": "token idea",
        "label": "field 1",
        "component": "textarea-field",
        "helperText": "Don't look.",
        "initialValue": "",
    },
    {
        "name": "name",
        "label": "field 1",
        "component": "textarea-field",
        "helperText": "That's not my name.",
        "initialValue": "{{product.artifacts.testk}}",
        "isSubstitution": True,
    },
    {
        "name": "optional",
        "label": "field 1",
        "component": "textarea-field",
        "helperText": "An optional field",
    },
]

_BASE = {"schema": {"fields": _FIELDS}}


@pytest.mark.django_db
def test_sanitize_parameters_for_secrets():
    service_parameters = {
        "name": "Joe",
        "Totally not a pass": "s3crete",
        "token idea": "my secret",
    }

    service_plan = ServicePlanFactory(base_schema=_BASE)

    svc = SanitizeParameters(service_plan, service_parameters).process()
    assert svc.sanitized_parameters == {
        "name": "Joe",
        "Totally not a pass": "$protected$",
        "token idea": "$protected$",
    }


@pytest.mark.django_db
def test_sanitize_parameters_optional_but_empty():
    service_parameters = {
        "name": "Joe",
        "Totally not a pass": "s3crete",
        "token idea": "my secret",
        "optional": None,
    }

    service_plan = ServicePlanFactory(base_schema=_BASE)

    svc = SanitizeParameters(service_plan, service_parameters).process()
    assert svc.sanitized_parameters == {
        "name": "Joe",
        "Totally not a pass": "$protected$",
        "token idea": "$protected$",
    }


@pytest.mark.django_db
def test_sanitize_parameters_required_but_empty():
    service_parameters = {
        "name": "Joe",
        "Totally not a pass": None,
        "token idea": "my secret",
    }

    service_plan = ServicePlanFactory(base_schema=_BASE)

    with pytest.raises(BadParamsException):
        SanitizeParameters(service_plan, service_parameters).process()


@pytest.mark.django_db
def test_sanitize_parameters_required_but_missing():
    service_parameters = {
        "name": "Joe",
        "token idea": "my secret",
    }

    service_plan = ServicePlanFactory(base_schema=_BASE)

    with pytest.raises(BadParamsException):
        SanitizeParameters(service_plan, service_parameters).process()
