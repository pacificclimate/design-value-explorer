import math


def sigfigs(x, n=3):
    """Round a float to specified number of significant figures (decimal)."""
    if not isinstance(x, float):
        return x
    if x == 0:
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))
