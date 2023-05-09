def copy(d: dict | list) -> dict | list:
    # dict case, iterate over items, copying the value and inserting it into frest
    # dict at the corresponding key.
    if isinstance(d, dict):
        result = {}
        for k, v in d.items():
            result[k] = copy(v)
        return result

    # list case iterates over items, appending them to a freshly instantiated list
    elif isinstance(d, list):
        result = []
        for item in d:
            result.append(copy(item))
        return result

    # any other type is returned as-is
    else:
        return d
