from climpyrical.gridding import (
    find_nearest_index,
    flatten_coords,
    transform_coords,
)
import numpy as np
import plotly.graph_objects as go
from dve.math_utils import nice_delta, nice_bounds


def lonlat_overlay(
    rlon_grid_size,
    rlat_grid_size,
    viewport=None,
    num_lon_intervals=6,
    num_lat_intervals=5,
    lon_round_to=(1, 2, 3, 5, 10, 15),
    lat_round_to=(1, 2, 3, 5, 10, 15),
    grid_lon_min=360 - 140,
    grid_lon_max=360 - 50,
    grid_lat_min=45,
    grid_lat_max=85,
):
    """
    Returns a list of graphical objects that render latitude and longitude lines
    in the map graph.

    Lat and lon lines are generated to cover the entire area defined by args
    `grid_lon_min`, `grid_lon_max`, `grid_lat_min`, `grid_lat_max`, which is
    by default the entire extent of Canada. The density of lines is determined
    by the viewport they will be shown in, but not the extent of them. This
    facilitates panning without reloading the map.

    Lines are constructed (I think) by creating "dotted lines" at the resolution
    of the grid scale, and plotting these across the map. It's not clear why
    you can't just plot a single line rather than "dots" ... style perhaps?
    This is almost certainly a horrible way to do this, but it suffices for now.

    :param rlat_grid_size: (int) Size of lon grid in underlying dataset.
    :param rlon_grid_size: (int) Size of lat grid in underlying dataset.
            It's not clear why these grid dimensions are used but that's how
            the code works.
    :param viewport: (dict) Viewport corners/bounds in rotated pole coordinates.
    :param num_lon_intervals: (int) Number of intervals of longitude in overlay.
    :param num_lat_intervals: (int) Number of intervals of latitude in overlay.
    :param lon_round_to: (list) Values of longitude increment to use.
    :param lat_round_to: (list) Values of latitude increment to use.
    :return: (list) Graphical objects representing lon-lat overlay.
    """
    if viewport is None:
        # Default (max zoom; full area) lon and lat bounds
        vp_lon_min = grid_lon_min
        vp_lon_max = grid_lon_max
        vp_lat_min = grid_lat_min
        vp_lat_max = grid_lat_max
    else:
        # Transform rotated pole viewport corners to standard lon-lat
        vp_x_range, vp_y_range = transform_coords(
            np.array([viewport["x_min"], viewport["x_max"]]),
            np.array([viewport["y_min"], viewport["y_max"]]),
            source_crs={
                "proj": "ob_tran",
                "o_proj": "longlat",
                "lon_0": -97,
                "o_lat_p": 42.5,
                "a": 6378137,
                "to_meter": 0.0174532925199,
                "no_defs": True,
            },
            target_crs={"init": "epsg:4326"},
        )
        vp_lon_min, vp_lon_max = 360 + vp_x_range
        vp_lat_min, vp_lat_max = vp_y_range

    # Compute "nice" lines of lon and lat in standard coordinates.
    # "Nice" means an increment between lines of one of the preferred values,
    # and lines at multiples of the increment.

    vp_lon_delta = nice_delta(
        vp_lon_min, vp_lon_max, num_lon_intervals, lon_round_to
    )
    grid_lon_min, grid_lon_max, num_grid_lon_intervals = nice_bounds(
        grid_lon_min, grid_lon_max, vp_lon_delta
    )
    lon_lines = np.linspace(
        grid_lon_min, grid_lon_max, num_grid_lon_intervals + 1
    )

    vp_lat_delta = nice_delta(
        vp_lat_min, vp_lat_max, num_lat_intervals, lat_round_to
    )
    grid_lat_min, grid_lat_max, num_grid_lat_intervals = nice_bounds(
        grid_lat_min, grid_lat_max, vp_lat_delta
    )
    lat_lines = np.linspace(
        grid_lat_min, grid_lat_max, num_grid_lat_intervals + 1
    )

    # This is where the craziness begins.
    # Compute x and y coordinates for lines of latitude.
    x_lat_line = np.linspace(lon_lines.min(), lon_lines.max(), rlon_grid_size)
    y_lat_line = [np.ones(rlon_grid_size) * latline for latline in lat_lines]

    # Compute x and y coordinates for lines of longitude.
    x_lon_line = [np.ones(rlat_grid_size) * lonline for lonline in lon_lines]
    y_lon_line = np.linspace(lat_lines.min(), lon_lines.max(), rlat_grid_size)

    # "Dotted line" rotated pole coordinates for lines of longitude
    rp_x_lon_line, rp_y_lon_line = [], []
    for x in x_lon_line:
        rp_x, rp_y = transform_coords(x, y_lon_line)
        rp_x = np.append(rp_x[::10], None)
        rp_y = np.append(rp_y[::10], None)
        rp_x_lon_line.append(rp_x)
        rp_y_lon_line.append(rp_y)
    rp_x_lon_line = np.array(rp_x_lon_line).flatten()
    rp_y_lon_line = np.array(rp_y_lon_line).flatten()

    # "Dotted line" rotated pole coordinates for lines of latitude
    rp_x_lat_line, rp_y_lat_line = [], []
    for y in y_lat_line:
        rp_x, rp_y = transform_coords(x_lat_line, y)
        rp_x = np.append(rp_x[::10], None)
        rp_y = np.append(rp_y[::10], None)
        rp_x_lat_line.append(rp_x)
        rp_y_lat_line.append(rp_y)
    rp_x_lat_line = np.array(rp_x_lat_line).flatten()
    rp_y_lat_line = np.array(rp_y_lat_line).flatten()

    # Text for labelling lines of lon, lat (at intersections)
    plon, plat = flatten_coords(lon_lines, lat_lines)
    prlon, prlat = transform_coords(plon, plat)
    lattext = [
        str(int(latval)) + "N" + ", " + str(int(360 - lonval)) + "W"
        for latval, lonval in zip(plat, plon)
    ]

    return [
        # Longitude lines
        go.Scattergl(
            x=rp_x_lon_line,
            y=rp_y_lon_line,
            mode="lines",
            hoverinfo="skip",
            visible=True,
            name="",
            line=dict(width=1, color="grey", dash="dash"),
        ),
        # Latitude lines
        go.Scattergl(
            x=rp_x_lat_line,
            y=rp_y_lat_line,
            mode="lines+text",
            hoverinfo="skip",
            visible=True,
            name="",
            line=dict(width=1, color="grey", dash="dash"),
        ),
        # Labels for lon/lat lines
        go.Scattergl(
            x=prlon,
            y=prlat,
            mode="text",
            text=lattext,
            hoverinfo="skip",
            visible=True,
            name="",
        ),
    ]
