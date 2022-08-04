import copy
import pytest
from dve.dict_utils import path_get, path_set

d0 = {}
d1 = {"a": {"b": {"c": 42}}}


@pytest.mark.parametrize(
    "d, path, default, expected",
    [
        (d1, ["a"], None, d1["a"]),
        (d1, ["a", "b"], None, d1["a"]["b"]),
        (d1, ["a", "b", "c"], None, d1["a"]["b"]["c"]),
        (d1, ["x"], None, None),
        (d1, ["a", "x"], None, None),
        (d1, ["a", "b", "x"], None, None),
        (d1, ["x", "y"], None, None),
        (d1, ["a", "b", "c", "x"], None, None),
        (d1, "a", None, d1["a"]),
        (d1, "a.b", None, d1["a"]["b"]),
        (d1, "a.b.c", None, d1["a"]["b"]["c"]),
        (d1, "x", None, None),
        (d1, "a.x", None, None),
        (d1, "a.b.x", None, None),
        (d1, "a.b.c.x", None, None),
    ],
)
def test_path_get(d, path, default, expected):
    assert path_get(d, path, default) == expected


@pytest.mark.parametrize(
    "d, path, value, expected",
    [
        (d0, "a", 99, {"a": 99}),
        (d0, "a.b", 99, {"a": {"b": 99}}),
        (d1, "a", 99, {"a": 99}),
        (d1, "a.b", 99, {"a": {"b": 99}}),
        (d1, "a.b.c", 99, {"a": {"b": {"c": 99}}}),
        (d1, "x", 99, {"a": {"b": {"c": 42}}, "x": 99}),
        (d1, "a.x", 99, {"a": {"b": {"c": 42}, "x": 99}}),
        (d1, "a.b.x", 99, {"a": {"b": {"c": 42, "x": 99}}}),
        (d1, "a.b.c.x", 99, {"a": {"b": {"c": {"x": 99}}}}),
    ],
)
def test_path_set(d, path, value, expected):
    e = copy.deepcopy(d)
    path_set(e, path, value)
    assert e == expected
