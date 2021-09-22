""" Collection of tag resources. """
import logging
from django.utils.translation import gettext_lazy as _

from ansible_catalog.main.inventory.services.collect_inventory_tags import (
    CollectInventoryTags,
)

logger = logging.getLogger("catalog")


class CollectTagResources:
    """Collection of collect inventories"""

    def __init__(self, order):
        self.order = order
        self.tag_resources = []

    def process(self):
        self.consolidate_inventory_tags()

        logger.info("Applied Tags: %s", self.tag_resources)
        return self

    def consolidate_inventory_tags(self):
        self.__collect_local_tags()
        self.__collect_remote_tags()

    def __collect_local_tags(self):
        visited = set()

        for item in self.order.order_items:
            if item.portfolio_item.portfolio.id in visited:
                return

            self.tag_resources += self.__tag_resources(
                item.portfolio_item.portfolio
            )
            visited.add(item.portfolio_item.portfolio.id)

            self.tag_resources += self.__tag_resources(item.portfolio_item)

        logger.info(" Applied Local Tags: %s", self.tag_resources)

    def __collect_remote_tags(self):
        visited = set()

        for item in self.order.order_items:
            if item.portfolio_item.service_offering_ref in visited:
                return

            visited.add(item.portfolio_item.service_offering_ref)
            self.__collect_remote_order_item_tags(item)

    def __collect_remote_order_item_tags(self, order_item):
        service_offering_id = str(
            order_item.portfolio_item.service_offering_ref
        )

        if service_offering_id is None:
            raise RuntimeError(
                _("ServiceOffering object {} not found").format(
                    service_offering_id
                )
            )

        tags = CollectInventoryTags(service_offering_id).process().tags()
        if tags:
            tag_resource = {
                "app_name": "inventory",
                "object_type": "ServiceInventory",
                "tags": [dict(name=tag) for tag in tags],
            }

            logger.info(" Applied Remote Tags: %s", tag_resource)

            self.tag_resources += [tag_resource]

    def __tag_resources(self, obj):
        tags = [tag.name for tag in obj.tag_resources]

        if tags:
            return [
                {
                    "app_name": "catalog",
                    "object_type": obj.__class__.__name__,
                    "tags": [dict(name=tag) for tag in tags],
                }
            ]
        else:
            return []
