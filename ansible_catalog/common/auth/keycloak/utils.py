def to_lower_camel(name):
    head, *tail = name.split("_")
    return head.lower() + "".join(x.title() for x in tail)
