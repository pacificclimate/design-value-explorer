import matplotlib
import numpy as np


def matplotlib_to_plotly(cmap, pl_entries):
    h = 1.0 / (pl_entries - 1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = list(map(np.uint8, np.array(cmap(k * h)[:3]) * 255))
        pl_colorscale.append([k * h, "rgb" + str((C[0], C[1], C[2]))])

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
