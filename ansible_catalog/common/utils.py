def removeprefix(string: str, prefix: str, /) -> str:
    if string.startswith(prefix):
        return string[len(prefix) :]
    else:
        return string