def to_lower_camel(name: str) -> str:
    """Converts snake_case string into lowerCamelCase."""
    head, *tail = name.split("_")
    return head.lower() + "".join(x.title() for x in tail)
