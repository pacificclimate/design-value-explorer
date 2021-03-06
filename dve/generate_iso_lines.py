from climpyrical.gridding import (
    find_nearest_index,
    flatten_coords,
    transform_coords,
)
import numpy as np
import plotly.graph_objects as go


def gen_lines(ds, X, Y):
    latlines = np.linspace(45, 85, 9)
    lonlines = np.linspace(225, 305, 12)

    plon, plat = flatten_coords(lonlines, latlines)
    prlon, prlat = transform_coords(plon, plat)

    latliney = [np.ones(ds.rlon.values.size) * latline for latline in latlines]
    latlinex = np.linspace(
        lonlines.min() - 3, lonlines.max() + 3, ds.rlon.values.size
    )

    lonlinex = [np.ones(ds.rlat.size) * lonline for lonline in lonlines]
    lonliney = np.linspace(latlines.min(), lonlines.max(), ds.rlat.size)

    lxarr, lyarr = [], []
    txarr, tyarr = [], []

    for lonline in lonlinex:
        lx, ly = transform_coords(lonline, lonliney)
        lx = np.append(lx[::10], None)
        ly = np.append(ly[::10], None)
        lxarr.append(lx)
        lyarr.append(ly)

    for latline in latliney:
        tx, ty = transform_coords(latlinex, latline)
        tx = np.append(tx[::10], None)
        ty = np.append(ty[::10], None)
        txarr.append(tx)
        tyarr.append(ty)

    lxarr = np.array(lxarr).flatten()
    lyarr = np.array(lyarr).flatten()
    txarr = np.array(txarr).flatten()
    tyarr = np.array(tyarr).flatten()

    lattext = [
        str(int(latval)) + "N" + ", " + str(int(360 - lonval)) + "W"
        for latval, lonval in zip(plat, plon)
    ]

    go_list = [
        go.Scattergl(
            x=lxarr,
            y=lyarr,
            mode="lines",
            hoverinfo="skip",
            visible=True,
            name="",
            line=dict(width=1, color="grey", dash="dash"),
        ),
        go.Scattergl(
            x=txarr,
            y=tyarr,
            mode="lines+text",
            hoverinfo="skip",
            visible=True,
            name="",
            line=dict(width=1, color="grey", dash="dash"),
        ),
        go.Scattergl(
            x=prlon,
            y=prlat,
            mode="text",
            text=lattext,
            hoverinfo="skip",
            visible=True,
            name="",
        ),

        # TODO: Move out of here
        go.Scattergl(
            x=X,
            y=Y,
            mode="lines",
            hoverinfo="skip",
            visible=True,
            name="",
            line=dict(width=0.5, color="black"),
        ),
    ]

    return go_list
