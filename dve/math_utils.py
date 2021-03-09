import math


def compact(items):
    return (item for item in items if item is not None)


def nearest(values, value):
    """
    Return the nearest element of `values` to `value`.
    This could be implemented *much* more efficiently, but since `values`
    typically contains fewer than 10 items, it is not worth the trouble.
    """
    diffs = tuple(abs(v - value) for v in values)
    min_diff = min(diffs)
    min_index = diffs.index(min_diff)
    return values[min_index]


def round_to_multiple(value, multiple, direction="nearest"):
    """Return multiple of `multiple` nearest to `value`."""
    try:
        f = {"down": math.floor, "nearest": round, "up": math.ceil}[direction]
    except KeyError:
        f = round
    return f(value/multiple) * multiple


def nice(low, high, num_intervals, round_to):
    """
    Return "nice" low, high, and num_intervals from non-nice values of
    same, and preferred increment values.

    :param low:
    :param high:
    :param num_intervals:
    :param round_to:
    :return:
    """
    delta = nearest(round_to, (high - low) / num_intervals)
    low = round_to_multiple(low, delta, direction="down")
    high = round_to_multiple(high, delta, direction="up")
    num_intervals = round((high - low) / delta)
    return low, high, num_intervals


def sigfigs(x, n=3):
    """Round a float to specified number of significant figures (decimal)."""
    if not isinstance(x, float):
        return x
    if x == 0:
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))
