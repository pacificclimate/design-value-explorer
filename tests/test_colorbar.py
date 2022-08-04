import math

import pytest
from dve.colorbar import uniformly_spaced_with_target, scale_transform


@pytest.mark.parametrize(
    "zmin, zmax, num_values, target, scale",
    [
        (0, 10, 11, 2, "linear"),
        (0, 10, 10, 2, "linear"),
        (0, 10, 12, 2, "linear"),
        (1, 10, 12, 2, "linear"),
        (-5, 5, 11, 0, "linear"),
        (-5, 5, 10, 0, "linear"),
        (1, 1e6, 7, 1e3, "logarithmic"),
        (2, 1e6, 7, 1e3, "logarithmic"),
        (1e-3, 1e3, 7, 1, "logarithmic"),
        (1e-4, 1e3, 7, 1, "logarithmic"),
        (0.791, 1.156, 10 + 1, 1, "logarithmic"),
    ],
)
def test_uniformly_spaced_with_target(zmin, zmax, num_values, target, scale):
    z = uniformly_spaced_with_target(zmin, zmax, num_values, target, scale)
    print(f"{z}")
    n = len(z)
    assert n in {num_values, num_values + 1}
    assert z[0] <= zmin <= z[1]
    assert z[n - 2] <= zmax <= z[n - 1]
    assert target in z
    # Check interval length -- in transformed space
    fwd, back = scale_transform(scale)
    dz = (fwd(zmax) - fwd(zmin)) / (num_values - 1)
    dzp = fwd(z[1]) - fwd(z[0])
    assert math.isclose(dz, dzp)
