""" Collection of tag resources. """
import logging
from django.utils.translation import gettext_lazy as _

from main.inventory.services.collect_inventory_tags import CollectInventoryTags

logger = logging.getLogger("catalog")


class CollectTagResources:
    """Collection of collect inventories"""

    def __init__(self, order_item):
        self.order_item = order_item
        self.tag_resources = []

    def process(self):
        self.consolidate_inventory_tags()

        logger.info(f"Applied Tags {self.tag_resources}")
        return self

    def consolidate_inventory_tags(self):
        self.__collect_local_tags()
        self.__collect_remote_tags()

    def __collect_local_tags(self):
        for item in self.order_item.order.order_items:
            self.tag_resources += self.__tag_resources(
                item.portfolio_item.portfolio
            )
            self.tag_resources += self.__tag_resources(item.portfolio_item)

        logger.info(f" Applied Local Tags {self.tag_resources}")

    def __collect_remote_tags(self):
        service_offering_id = str(
            self.order_item.portfolio_item.service_offering_ref
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

            logger.info(f" Applied Remote Tags {tag_resource}")

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
