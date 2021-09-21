import pytest
from dve.config import path_get

d1 = {
    "a": {
        "b": {
            "c": 42,
        }
    }
}

@pytest.mark.parametrize(
    "d, path, default, expected",
    [
        (d1, "a", None, d1["a"]),
        (d1, ["a"], None, d1["a"]),
        (d1, ["a", "b"], None, d1["a"]["b"]),
        (d1, ["a", "b", "c"], None, d1["a"]["b"]["c"]),
        (d1, "x", None, None),
        (d1, ["x"], None, None),
        (d1, ["a", "x"], None, None),
        (d1, ["a", "b", "x"], None, None),
        (d1, ["a", "b", "c", "x"], None, None),
    ]
)
def test_path_get(d, path, default, expected):
    assert path_get(d, path, default) == expected