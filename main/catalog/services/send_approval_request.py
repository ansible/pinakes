from django.utils import timezone
from main.models import Tenant
from main.catalog.models import Order, OrderItem


class SendApprovalRequest:
    def __init__(user, order):
        self.user = user
        self.order_item = OrderItem.objects.filter(order_id=order.id).first()

    def process(self):
        self.order_item.state = OrderItem.State.PENDING
        self.order_item.request_sent_at = timezone.now()
        self.order_item.save()
        return
