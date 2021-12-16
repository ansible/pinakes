""" Compare service plans. """

import logging

from ansible_catalog.main.inventory.services.get_service_offering import (
    GetServiceOffering,
)

logger = logging.getLogger("catalog")


class CompareServicePlans:
    """Compare service plans"""

    def __init__(self, service_plan):
        self.base_schema = service_plan.base_schema
        self.service_offering_ref = (
            service_plan.portfolio_item.service_offering_ref
        )

    @classmethod
    def is_changed(cls, plan):
        if cls.is_empty(plan):
            return False

        potential = cls(plan)
        inventory_schema, schema_sha256 = potential._inventory_base()

        if plan.base_sha256 != schema_sha256:  # Survey is changed by Tower
            if plan.modified:
                plan.outdated = True
                plan.outdated_message = potential._compare_schema_fields(
                    inventory_schema
                )
            else:  # resync with the remote
                plan.outdated = False
                plan.base_schema = inventory_schema
                plan.modified_schema = None
                plan.base_sha256 = schema_sha256

            plan.save()
        else:
            if plan.modified:  # only user modified
                plan.outdated = True
                plan.outdated_message = potential._compare_schema_fields(
                    inventory_schema
                )
                plan.save()

        return plan.outdated

    @classmethod
    def any_changed(cls, plans):
        changed = [plan for plan in plans if cls.is_changed(plan)]

        return len(changed) > 0

    @classmethod
    def changed_plans(cls, plans):
        return [plan for plan in plans if cls.is_changed(plan)]

    @classmethod
    def is_empty(cls, plan):
        if plan.base_schema is None:
            return True

        schema_type = plan.base_schema.get("schemaType", None)

        return schema_type is None or schema_type == "emptySchema"

    def _inventory_base(self):
        svc = GetServiceOffering(self.service_offering_ref, True).process()
        plan = svc.service_plans.first()
        return (
            (plan.create_json_schema, plan.schema_sha256) if plan else ({}, "")
        )

    def _compare_schema_fields(self, inventory_schema):
        message = "Schema fields changes have been detected: "

        # remote schema fields and field names
        inventory_fields = inventory_schema.get("schema", {}).get("fields")
        inventory_field_names = [
            field.get("name") for field in inventory_fields
        ]

        # local schema fields and field names
        base_fields = self.base_schema.get("schema", {}).get("fields")
        base_field_names = [field.get("name") for field in base_fields]

        common_field_names = list(
            set(inventory_field_names) & set(base_field_names)
        )

        if len(common_field_names) == 0:  # no same field
            message += "fields added: %s; fields removed: %s" % (
                inventory_field_names,
                base_field_names,
            )
        # remote and local have same fields in names
        elif set(inventory_field_names) == set(base_field_names):
            changed_field_names = self._changed_field_names(
                base_fields, inventory_fields, base_field_names
            )
            if len(changed_field_names) != 0:
                message += "fields changed: %s" % changed_field_names
        else:
            add_field_names = list(
                set(inventory_field_names) - set(common_field_names)
            )
            removed_field_names = list(
                set(base_field_names) - set(common_field_names)
            )
            message += "fields added: %s; fields removed: %s; " % (
                add_field_names,
                removed_field_names,
            )
            changed_field_names = self._changed_field_names(
                base_fields, inventory_fields, common_field_names
            )

            if len(changed_field_names) != 0:
                message += "fields changed: %s" % changed_field_names

        return message

    def _changed_field_names(
        self, local_fields, remote_fields, compare_field_names
    ):
        changed = []

        for name in compare_field_names:
            local_field = self._get_field_by_name(local_fields, name)
            remote_field = self._get_field_by_name(remote_fields, name)
            if not self._is_same_field(local_field, remote_field):
                changed.append(name)

        return changed

    def _get_field_by_name(self, fields, name):
        for field in fields:
            if field.get("name") == name:
                return field

        return None

    def _is_same_field(self, local_field, remote_field):
        # compare field's keys first
        if local_field.keys() == remote_field.keys():
            for key in local_field.keys():
                if local_field.get(key) != remote_field.get(key):
                    return False

            return True

        return False
