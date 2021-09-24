def path_get(d, path, default=None, separator="."):
    """
    Get a value addressed by `path` from a dict `d`.
    If `path` is not valid within the dict, return `default`.
    """
    if not isinstance(d, dict):
        return default
    if isinstance(path, str):
        return path_get(d, path.split(separator), default)
    if isinstance(path, (list, tuple)):
        if len(path) == 1:
            return d.get(path[0], default)
        return path_get(d[path[0]], path[1:], default)


