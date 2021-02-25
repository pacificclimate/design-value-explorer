import matplotlib
import numpy as np


def matplotlib_to_plotly(cmap, vmin, vmax, N):
    # h = 1.0 / (pl_entries - 1)
    ticks = np.linspace(0, 1, N+1)
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
    if len(bvals) != len(colors)+1:
        raise ValueError(
            'len(boundary values) should be equal to  len(colors)+1'
        )
    bvals = sorted(bvals)     
    normalized_vals = [(v-bvals[0])/(bvals[-1]-bvals[0]) for v in bvals]
    
    discrete_colorscale = []
    for k in range(len(colors)):
        discrete_colorscale.extend(
            [
                [normalized_vals[k], colors[k]],
                [normalized_vals[k+1], colors[k]]
            ]
        )

    return discrete_colorscale
