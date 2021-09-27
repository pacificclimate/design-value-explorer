def path_get(d, path, default=None, separator="."):
    """
    Get a value addressed by `path` from dict `d`.
    If `path` is not valid within the dict, return `default`.
    """
    if not isinstance(d, dict):
        return default
    if isinstance(path, str):
        return path_get(d, path.split(separator), default)
    if isinstance(path, (list, tuple)):
        head = path[0]
        if len(path) == 1:
            return d.get(head, default)
        if head in d:
            return path_get(d[head], path[1:], default)
        return default


def path_set(d, path, value, separator="."):
    """
    Set a value addressed by `path` in dict `d`.
    If an element of `path` does not exist within the dict, create sub-dicts
    as necessary.
    """
    assert isinstance(d, dict)
    if isinstance(path, str):
        path_set(d, path.split(separator), value)
    if isinstance(path, (list, tuple)):
        key = path[0]
        if len(path) == 1:
            d[key] = value
        else:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            path_set(d[key], path[1:], value)

