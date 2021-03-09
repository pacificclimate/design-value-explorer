import math


def compact(items):
    return (item for item in items if item is not None)


def nearest(values, value):
    """Return the nearest element of `values` to `value`."""
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


def rounded(low, high, num_intervals, round_to):
    print(f"rounded({low}, {high}, {num_intervals}, {round_to})")
    delta = nearest(round_to, (high - low) / num_intervals)
    print(f"delta={delta}")
    low = round_to_multiple(low, delta, direction="down")
    high = round_to_multiple(high, delta, direction="up")
    num_intervals = round((high - low) / delta)
    print(f"rounded -> ({low}, {high}, {num_intervals})")
    return low, high, num_intervals


def sigfigs(x, n=3):
    """Round a float to specified number of significant figures (decimal)."""
    if not isinstance(x, float):
        return x
    if x == 0:
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))
