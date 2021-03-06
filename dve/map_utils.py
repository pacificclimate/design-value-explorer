"""
Utilities for processing data from maps.

Note: "Pointer data" (`pointer_data`) refers to data objects returned by
dcc.Graph in hoverData and clickData. These items describe the map (or any
chart) under the mouse pointer.
"""

from climpyrical.gridding import find_nearest_index


def pointer_rlonlat(pointer_data):
    """
    Return rotated pole coordinates (native map coords) specified in a
    pointer data object (see note above).

    :param pointer_data:
    :return: tuple(rlat, rlon)
    """
    if pointer_data is None:
        return None, None
    return tuple(pointer_data["points"][0][name] for name in ("x", "y"))


def rlonlat_to_rindices(dataset, rlon, rlat):
    """
    Return the indices in the rotated pole coordinate system corresponding to
    given rotated pole coordinates.

    :param dataset:
    :param rlon:
    :param rlat:
    :return: tuple(ilon, ilat)
    """
    ilon = find_nearest_index(dataset.rlon.values, rlon)
    ilat = find_nearest_index(dataset.rlat.values, rlat)
    return ilon, ilat


def pointer_rindices(pointer_data, dataset):
    """
    Return the indices in the rotated pole coordinate system of the position
    reported in the pointer data object (see note above).

    :param pointer_data:
    :param dataset:
    :return:
    """
    if pointer_data is None:
        return None, None
    # TODO: DRY
    rlon, rlat = (pointer_data["points"][0][name] for name in ("x", "y"))
    ilon = find_nearest_index(dataset.rlon.values, rlon)
    ilat = find_nearest_index(dataset.rlat.values, rlat)
    return ilon, ilat


def rindices_to_lonlat(dataset, ilon, ilat):
    """
    Return standard lonlat coordinates corresponding to rotated pole indices.

    :param dataset:
    :param ilon:
    :param ilat:
    :return:
    """
    if ilon is None or ilat is None:
        return None, None
    lat = dataset.lat.values[ilat, ilon]
    lon = dataset.lon.values[ilat, ilon] - 360
    return lon, lat


def pointer_value(pointer_data):
    """
    Return (z-) value reported by pointer data object (see note above), and
    an identifier of the source type (interpolated grid, station dataset).

    :param pointer_data:
    :return:
    """
    curve_number = pointer_data["points"][0]["curveNumber"]

    try:
        z = pointer_data["points"][0][{4: "z", 5: "text"}[curve_number]]
    except KeyError:
        z = None

    try:
        source = {4: "Interp", 5: "Station"}[curve_number]
    except KeyError:
        source = None

    return z, source
