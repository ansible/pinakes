import logging

logger = logging.getLogger("catalog")


def compare_schemas(source_schema, target_schema):
    """Compare target_schema with source_ schema
    @return empty string if they are the same, otherwise return changed content
    """

    message = "Schema fields changes have been detected: "
    changed_content = ""

    # remote schema fields and field names
    inventory_fields = target_schema.get("schema", {}).get("fields", [])
    inventory_field_names = [field.get("name") for field in inventory_fields]

    # local schema fields and field names
    base_fields = source_schema.get("schema", {}).get("fields", [])
    base_field_names = [field.get("name") for field in base_fields]

    common_field_names = list(
        set(inventory_field_names) & set(base_field_names)
    )

    if len(common_field_names) == 0:  # no same field
        if len(inventory_field_names) > 0:
            changed_content += f"fields added: {inventory_field_names}; "

        if len(base_field_names) > 0:
            changed_content += f"fields removed: {base_field_names}"
    # remote and local have same fields in names
    elif set(inventory_field_names) == set(base_field_names):
        changed_field_names = _changed_field_names(
            base_fields, inventory_fields, base_field_names
        )
        if len(changed_field_names) != 0:
            changed_content += f"fields changed: {changed_field_names}"
    else:
        add_field_names = list(
            set(inventory_field_names) - set(common_field_names)
        )
        removed_field_names = list(
            set(base_field_names) - set(common_field_names)
        )
        changed_field_names = _changed_field_names(
            base_fields, inventory_fields, common_field_names
        )

        if len(add_field_names) > 0:
            changed_content += f"fields added: {add_field_names}; "

        if len(removed_field_names) > 0:
            changed_content += f"fields removed: {removed_field_names}; "

        if len(changed_field_names) != 0:
            changed_content += f"fields changed: {changed_field_names}"

    return (
        changed_content if changed_content == "" else message + changed_content
    )


def _changed_field_names(local_fields, remote_fields, compare_field_names):
    changed = []

    for name in compare_field_names:
        local_field = _get_field_by_name(local_fields, name)
        remote_field = _get_field_by_name(remote_fields, name)
        if not _is_same_field(local_field, remote_field):
            changed.append(name)

    return changed


def _get_field_by_name(fields, name):
    for field in fields:
        if field.get("name") == name:
            return field

    return None


def _is_same_field(local_field, remote_field):
    # compare field's keys first
    if local_field.keys() == remote_field.keys():
        for key in local_field.keys():
            if local_field.get(key) != remote_field.get(key):
                return False

        return True

    return False
