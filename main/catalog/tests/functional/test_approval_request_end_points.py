""" Test order end points """
import json
import pytest
from django.urls import reverse

from main.catalog.tests.factories import OrderItemFactory
from main.catalog.tests.factories import ApprovalRequestFactory


@pytest.mark.django_db
def test_order_item_approval_request_get(api_request):
    """Get List of approval requests of an order item"""
    approval_request = ApprovalRequestFactory()

    response = api_request(
        "get",
        reverse(
            "orderitem-approvalrequest-list",
            args=(approval_request.order_item.id,),
        ),
    )

    assert response.status_code == 200

    content = json.loads(response.content)
    assert content["count"] == 1
