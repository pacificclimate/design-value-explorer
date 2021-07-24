import logging
import matplotlib
import matplotlib.cm
import plotly.graph_objects as go
import numpy as np


logger = logging.getLogger("dve")


def matplotlib_to_plotly(cmap, vmin, vmax, N):
    # h = 1.0 / (pl_entries - 1)
    ticks = np.linspace(0, 1, N + 1)
    pl_colorscale = []

    for k in range(N):
        C = list(map(np.uint8, np.array(cmap(ticks[k])[:3]) * 255))
        pl_colorscale.append([ticks[k], "rgb" + str((C[0], C[1], C[2]))])

    return pl_colorscale


def get_cmap_divisions(colorscheme, n):
    n += 1
    magma_cmap = matplotlib.cm.get_cmap(colorscheme, n)
    norm = matplotlib.colors.Normalize(vmin=0, vmax=255)

    magma_rgb = []

    for i in range(0, 255):
        k = matplotlib.colors.colorConverter.to_rgb(magma_cmap(norm(i)))
        magma_rgb.append(k)

    magma = matplotlib_to_plotly(magma_cmap, n)
    new_magma = []
    for i, color in enumerate(magma):
        if i < len(magma) - 1:
            new_magma.append(color)
            new_magma.append(magma[i + 1])

    nmcopy = []
    for i in range(len(new_magma)):
        if i < len(new_magma) - 1:
            nmcopy.append([new_magma[i][0], new_magma[i + 1][1]])

    nmcopy.append(magma[len(magma) - 1])
    return nmcopy


def plotly_discrete_colorscale(bvals, colors):
    """
    Create a Plotly discrete colourscale from a list of boundary values and
    colours.

    :param bvals: list of values bounding intervals to be coloured
    :param colors: list of rgb or hex colorcodes; color[k] colours interval
        [bvals[k], bvals[k+1]], 0 <= k < len(bvals)-1
    :return:

    Taken from:
    https://chart-studio.plotly.com/~empet/15229/heatmap-with-a-discrete-colorscale/#/
    """
    if len(bvals) != len(colors) + 1:
        raise ValueError(
            "len(boundary values) should be equal to  len(colors)+1"
        )
    bvals = sorted(bvals)
    normalized_vals = [(v - bvals[0]) / (bvals[-1] - bvals[0]) for v in bvals]

    discrete_colorscale = []
    for k in range(len(colors)):
        discrete_colorscale.extend(
            [
                [normalized_vals[k], colors[k]],
                [normalized_vals[k + 1], colors[k]],
            ]
        )

    return discrete_colorscale


def colorscale_boundaries(zmin, zmax, num_colours, scale):
    """
    Return a list of num_colours + 1 uniformly spaced colourscale boundaries
    spanning the specified range of values, inclusive. "Uniformly" here means
    either linear or geometric (for a log-scale display), according as `scale`
    == "linear" or "logarithmic".

    :param zmin: minimum data value
    :param zmax: maximum data value
    :param num_colours: number of colours (intervals)
    :param scale: "linear" or "logarithmic"
    :return: list of boundary values of length num_colours + 1
    """
    if scale == "logarithmic":
        return 10 ** np.linspace(
            np.log10(zmin), np.log10(zmax), num_colours + 1
        )
    else:
        return np.linspace(zmin, zmax, num_colours + 1)


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


def scale_transform(scale):
    return (
        {
            "linear": lambda x: x,
            "logarithmic": np.log10,
        }[scale],
        {
            "linear": lambda x: x,
            "logarithmic": lambda x: 10 ** x,
        }[scale]
    )


def colorscale_colorbar(colors, zmin, zmax, scale, tickvals, ticktext, **kwargs):
    colors = list(colors)
    num_colours = len(colors)
    # TODO: Compute this by normalizing boundaries
    norm_boundaries = np.linspace(0, 1, num_colours + 1)
    colorscale = plotly_discrete_colorscale(norm_boundaries, colors)
    transform, _ = scale_transform(scale)
    # TODO: Compute this by transforming boundaries
    t_boundaries = np.linspace(transform(zmin), transform(zmax), num_colours + 1)
    midpoints = (t_boundaries[1:] + t_boundaries[:-1]) / 2
    logger.debug(f"{num_colours} colours: {colors}")
    logger.debug(f"midpoints: {midpoints}")
    return go.Figure(
        data=go.Heatmap(
            x=[""],
            y=midpoints,
            z=[[z] for z in midpoints],
            colorscale=colorscale,
            showscale=False,
            hoverinfo="skip",
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
                tickvals=[transform(v) for v in tickvals],
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
            )
        ),
        **kwargs,
    )


def midpoint_ticks(zmin, zmax, scale, num_colours):
    fwd, back = scale_transform(scale)
    # TODO: Compute this by transforming boundaries
    t_boundaries = np.linspace(fwd(zmin), fwd(zmax), num_colours + 1)
    midpoints = (t_boundaries[1:] + t_boundaries[:-1]) / 2
    return back(midpoints)


def boundary_ticks(zmin, zmax, scale, num_colours):
    fwd, back = scale_transform(scale)
    # TODO: Compute this by transforming boundaries
    t_boundaries = np.linspace(fwd(zmin), fwd(zmax), num_colours + 1)
    return back(t_boundaries)


def use_ticks(zmin, zmax, scale, num_colours, max_num_ticks):
    if num_colours <= max_num_ticks:
        return boundary_ticks(zmin, zmax, scale, num_colours)
    return boundary_ticks(zmin, zmax, scale, max_num_ticks)