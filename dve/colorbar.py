import logging
import math

import matplotlib
import matplotlib.cm
import plotly.graph_objects as go
import numpy as np

from dve.math_utils import nearest

logger = logging.getLogger("dve")


# The map can be displayed with either a linear or logarithmic colorscale.
# Unfortunately, continuous logarithmic colorscales are not available directly
# from Plotly, so we must roll our own. Also, their "logarithmic" option on
# colorbars is completely unsuited to our application, so we must roll
# our own colorbar too.
#
# The map is therefore displayed using a "discrete colorscale", which is a
# colorscale in which data values are mapped to a set of discrete (not
# continuous or interpolated) colors. In particular, we map appropriately
# selected data value intervals onto colors. For information on this, see
# https://plotly.com/python/colorscales/, sections "Custom Discretized Heatmap
# Color scale with Graph Objects" and "Constructing a Discrete or Discontinuous
# Color Scale". To maintain uniform appearance and behaviour, both linear and
# logarithmic colorscales are implemented via a discrete colorscale, even though
# continuous linear colorscales are available in plotly.


def normalize(a):
    a = list(a)
    diff = a[-1] - a[0]
    return [(v - a[0]) / diff for v in a]


def discrete_colorscale(bvals, colors):
    """
    Create a Plotly discrete colourscale from a list of interval boundary values
    and colours.

    :param bvals: list of values bounding intervals to be coloured
    :param colors: list of colorcodes; color[k] colours interval
        [bvals[k], bvals[k+1]], 0 <= k < len(bvals)-1
    :return:
    """
    if len(bvals) != len(colors) + 1:
        raise ValueError(
            "len(boundary values) should be equal to  len(colors)+1"
        )
    nvals = normalize(bvals)
    return [
        endpt
        for interval in zip(zip(nvals[:-1], colors), zip(nvals[1:], colors))
        for endpt in interval
    ]


def scale_transform(scale):
    """
    Return transform functions forward (from natural to transformed space)
    and backward (from transformed to natural space) for scale. These are
    numpy functions, so can be applied to numpy arrays.

    :param scale: "linear" or "logarithmic"
    :return: 2-tuple: (forward, back)
    """
    try:
        return {
            "linear": (lambda x: x, lambda x: x),
            "logarithmic": (np.log10, lambda x: 10 ** x),
        }[scale]
    except KeyError:
        raise ValueError(
            f"scale must be either 'linear' or 'logarithmic'; got {scale}"
        )


def uniformly_spaced_with_target(
    zmin, zmax, num_values, target=None, scale="linear"
):
    """
    Return an array of n in {num_values, num_values + 1} values, "uniformly"
    spaced between approximately zmin and zmax, with the target value, if
    specified (not None), guaranteed to be in the array.

    Note: "Uniformly" here means either a linear or geometric sequence,
    according as `scale` == "linear" or "logarithmic".

    This function is used to create boundary values for discrete color maps,
    and to create tick values for the same.

    If target is None, or if zmin, zmax, and num_values happen to hit the
    target value (within a small tolerance relative to the z-values), then
    the array length is n = num_values, and z[0] == zmin, z[n-1] == zmax.

    Otherwise, the array length is n = num_values + 1.

    Informally, the array has the same spacing as would the array without
    target, but values in the array are adjusted by the smallest amount possible
    such that the target is hit by some value in the array. This may add a
    single item at the beginning or end of the array depending on the value of
    the target.

    Formally:
    z[1] - z[0] == (zmax - zmin) / (num_values - 1),
    z[0] <= zmin <= z[1],
    z[n-2] <= zmax <= z[n-1],
    target in z.

    :param zmin: Minimum value
    :param zmax: Maximum value
    :param target: Target value
    :param num_values: Number of values
    :param scale: Name of scale ("linear" or "logarithmic")
    :return: numpy array of uniformly spaced values including target
    """
    fwd, back = scale_transform(scale)

    if target is None:
        return back(np.linspace(fwd(zmin), fwd(zmax), num_values))

    # Work in transformed value space
    z0, zn, v = map(fwd, (zmin, zmax, target))

    # Unadjusted values
    z = np.linspace(z0, zn, num_values)  # unadjusted array of values
    delta_z = (zn - z0) / (num_values - 1)  # == z[1] - z[0]
    k = int(round(v - z0) / delta_z)  # z[k] is closest to v
    d = v - z[k]

    # Targeted values
    d_islarge = not math.isclose(d / delta_z, 0, abs_tol=1e-3)
    d = d if d_islarge else 0
    before = [z0 - delta_z] if d_islarge and d > 0 else []
    after = [zn + delta_z] if d_islarge and d < 0 else []
    z_prime = np.concatenate((before, z, after)) + d

    # Transform back
    return back(z_prime)


def colorscale_colors(colour_map_name, num_colours):
    """
    Return a list of num_colours colour definitions (in hex notation)
    derived from a named matplotlib color map.

    :param colour_map_name: matplotlib colour map name
    :param num_colours: number of colours
    :return: list of strings containing hex colour definitions
    """
    cmap = matplotlib.cm.get_cmap(colour_map_name, num_colours)
    return [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]


def discrete_colorscale_colorbar(
    boundaries, colorscale, scale, tickvals, ticktext, **kwargs
):
    """
    Return a Plotly Figure that displays a vertical colourbar depicting a
    given discrete colorscale.

    The heatmap has 1 x-axis cells (identified by empty string), and
    num_colours = len(boundaries) - 1 = len(colorscale) / 2 y-axis cells.
    The z-values are the midpoints of the discrete colorscale boundary values,
    which ensures that each color in the colorscale is represented exactly once.
    The heatmap is of course displayed using the given colorscale.

    The colorbar is labelled on the right side by ticks specified by tickvals
    and ticktext. These labels are defined by the user, and for the most useful
    effect with a moderate number of colours should be a subset of the boundary
    values. For a large number of colours, which appears more like a continuous
    colorscale, the location of ticks can be more arbitrary.

    :param boundaries: numpy array of boundaries used to define the colorscale.
    :param colorscale: A plotly discrete colorscale.
    :param scale: "linear" or "logarithmic"
    :param tickvals: values where ticks (labels) should be placed
    :param ticktext: ticks (labels) for colorbar
    :param kwargs: further arts to be passed to the Figure
    :return: plotly.graphical_objects.Figure
    """
    fwd, back = scale_transform(scale)
    t_boundaries = fwd(boundaries)
    t_midpoints = (t_boundaries[1:] + t_boundaries[:-1]) / 2
    raw_midpoints = back(t_midpoints)
    return go.Figure(
        data=go.Heatmap(
            x=[""],
            y=t_midpoints,
            z=[[z] for z in raw_midpoints],
            colorscale=colorscale,
            showscale=False,
            hoverinfo="skip",
            # hovertemplate="%{z:3.2r}<extra></extra>",
        ),
        layout=go.Layout(
            xaxis=go.layout.XAxis(
                fixedrange=True,
                showline=True,
                linewidth=1,
                linecolor="black",
                mirror=True,
            ),
            yaxis=go.layout.YAxis(
                side="right",
                fixedrange=True,
                showline=True,
                linewidth=1,
                linecolor="black",
                mirror=True,
                tickmode="array",
                tickvals=[fwd(v) for v in tickvals],
                ticktext=ticktext,
            ),
            autosize=False,
            width=60,  # very sensitive; < 60 => no labels
            height=500,
            margin=go.layout.Margin(
                t=50,
                b=10,
                l=1,
                # yaxis width must be >= 60 for reasons unknown
                # adjust visual width of colorbar by adjusting right margin
                r=40,
            ),
        ),
        **kwargs,
    )


def use_ticks(zmin, zmax, target, scale, num_colours, max_num_ticks):
    """Pick a useful set of ticks."""
    return uniformly_spaced_with_target(
        zmin, zmax, min(num_colours + 1, max_num_ticks), target, scale
    )


def tick_roundto(tickvals):
    num_ticks = len(tickvals)
    tick_delta = (tickvals[-1] - tickvals[0]) / (num_ticks - 1)
    tick_delta_pow_10 = 10 ** math.floor(math.log10(tick_delta))
    tick_delta_mantissa = tick_delta / tick_delta_pow_10
    nice_mantissa = nearest((1, 2, 5), tick_delta_mantissa)
    roundto = nice_mantissa * tick_delta_pow_10
    logger.debug(f"tick rounding: "
                 f"num_ticks={num_ticks}, "
                 f"tick_delta_pow_10={tick_delta_pow_10}, "
                 f"tick_delta_mantissa={tick_delta_mantissa}, "
                 f"nice_mantissa={nice_mantissa}, "
                 f"tick_roundto={tick_roundto}, ")
    return roundto
