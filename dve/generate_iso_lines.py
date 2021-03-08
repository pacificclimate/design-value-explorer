from climpyrical.gridding import (
    find_nearest_index,
    flatten_coords,
    transform_coords,
)
import numpy as np
import plotly.graph_objects as go


def gen_lines(
    ds,
    lon_min = 225,
    lon_max = 305,
    num_lon_lines = 6,
    lat_min = 45,
    lat_max = 85,
    num_lat_lines = 5,
):
    """
    Returns a list of graphical objects that render latitude and longitude lines
    in the map graph.

    Lines are constructed (I think) by creating "dotted lines" at the resolution
    of the grid scale, and plotting these across the map. It's not clear why
    you can't just plot a single line rather than "dots" ... style perhaps?
    This is almost certainly a horrible way to do this, but it suffices for now.

    :param ds:
    :return:
    """
    # Lines of latitude and longitude to draw
    lat_lines = np.linspace(lat_min, lat_max, num_lat_lines)
    lon_lines = np.linspace(lon_min, lon_max, num_lon_lines)

    rlon_size = ds.rlon.values.size
    rlat_size = ds.rlat.size
    print(f"### rlon_size={rlon_size}, rlat_size={rlat_size}, ")
    # x and y coordinates for lines of latitude.
    # Why +/- 3?
    x_lat_line = np.linspace(
        lon_lines.min() - 3, lon_lines.max() + 3, rlon_size
    )
    y_lat_line = [np.ones(rlon_size) * latline for latline in lat_lines]

    # x and y coordinates for lines of longitude. Why does this need to be done?
    x_lon_line = [np.ones(rlat_size) * lonline for lonline in lon_lines]
    y_lon_line = np.linspace(lat_lines.min(), lon_lines.max(), rlat_size)

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
