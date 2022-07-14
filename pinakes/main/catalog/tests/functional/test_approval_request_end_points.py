"""Test order end points"""
import pytest

from pinakes.main.catalog.tests.factories import (
    ApprovalRequestFactory,
)


@pytest.mark.django_db
def test_order_approval_request_get(api_request):
    """Get List of approval requests of an order item"""
    approval_request = ApprovalRequestFactory()

    response = api_request(
        "get",
        "catalog:order-approvalrequests-list",
        approval_request.order.id,
    )

    assert response.status_code == 200

    data = response.data
    assert data["count"] == 1
    assert data["results"][0]["id"] == approval_request.id
    assert (
        data["results"][0]["approval_request_ref"]
        == approval_request.approval_request_ref
    )
    assert data["results"][0]["reason"] == approval_request.reason
