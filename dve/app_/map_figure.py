import json
import logging
from pkg_resources import resource_filename

from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

import geopandas as gpd
import matplotlib.cm
import numpy as np

from dve.data import get_data
from dve.colorbar import plotly_discrete_colorscale
from dve.generate_iso_lines import lonlat_overlay
from dve.processing import coord_prep

from climpyrical.data import read_data
from climpyrical.gridding import find_nearest_index
from climpyrical.mask import stratify_coords


logger = logging.getLogger("dve")


def add_callbacks(app, config):
    # Load Canada map polygons
    canada = gpd.read_file(
        resource_filename("dve", config["paths"]["canada_vector"])
    ).geometry
    canada_x, canada_y = stratify_coords(canada)

    # Bounds of Canada map
    cx_min = min(value for value in canada_x if value is not None)
    cx_max = max(value for value in canada_x if value is not None)
    cy_min = min(value for value in canada_y if value is not None)
    cy_max = max(value for value in canada_y if value is not None)

    native_mask = (
        read_data(resource_filename("dve", config["paths"]["native_mask"]))[
            "sftlf"
        ]
        >= 1.0
    )

    @app.callback(
        Output("my-graph", "figure"),
        [
            Input("mask-ctrl", "on"),
            Input("stations-ctrl", "on"),
            Input("design-value-id-ctrl", "value"),
            Input("cbar-slider", "value"),
            Input("colourbar-range-ctrl", "value"),
            Input("dataset-ctrl", "value"),
            Input("scale-ctrl", "value"),
            Input("colour-map-ctrl", "value"),
            Input("viewport-ds", "children"),
        ],
    )
    def update_ds(
        mask_ctrl,
        stations_ctrl,
        design_value_id_ctrl,
        cbar_slider,
        range_slider,
        dataset_ctrl,
        scale_ctrl,
        colour_map_ctrl,
        viewport_ds,
    ):
        empty_fig = {
            "layout": {
                "title": "Loading...",
                "font": dict(size=13, color="grey"),
                "height": 750,
                "uirevision": "None",
            }
        }

        # TODO: This appears not to happen any more. Remove if so.
        if range_slider is None:
            logger.debug("### update_ds: range_slider is None")
            return empty_fig

        viewport = viewport_ds and json.loads(viewport_ds)

        zmin = range_slider[0]
        zmax = range_slider[1]

        if scale_ctrl == "logarithmic":
            ticks = np.linspace(np.log10(zmin), np.log10(zmax), cbar_slider + 1)
            ticks = np.around(10 ** (ticks), 2)
        else:
            ticks = np.around(np.linspace(zmin, zmax, cbar_slider + 1), 3)

        cmap = matplotlib.cm.get_cmap(colour_map_ctrl, cbar_slider)

        colours = [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]

        discrete_colorscale = plotly_discrete_colorscale(ticks, colours)

        # TODO: Inline this unnecessary variable
        r_or_m = dataset_ctrl

        # TODO: Rename all this shit
        ds = get_data(config, design_value_id_ctrl, r_or_m)
        (dv,) = ds.data_vars  # TODO: Rename dv_var_name
        df = get_data(config, design_value_id_ctrl, "stations")
        station_dv = config["dvs"][design_value_id_ctrl]["station_dv"]

        # Index values for clipping data to Canada bounds
        icxmin = find_nearest_index(ds.rlon.values, cx_min)
        icxmax = find_nearest_index(ds.rlon.values, cx_max)
        icymin = find_nearest_index(ds.rlat.values, cy_min)
        icymax = find_nearest_index(ds.rlat.values, cy_max)

        go_list = []

        # Lon-lat overlay
        lonlat_overlay_config = config["map"]["lonlat_overlay"]
        go_list += lonlat_overlay(
            # It's not clear why the grid sizes should be taken from the
            # dataset, but that's how the code works. Ick.
            rlon_grid_size=ds.rlon.size,
            rlat_grid_size=ds.rlat.size,
            viewport=viewport,
            num_lon_intervals=lonlat_overlay_config["lon"]["num_intervals"],
            lon_round_to=lonlat_overlay_config["lon"]["round_to"],
            num_lat_intervals=lonlat_overlay_config["lat"]["num_intervals"],
            lat_round_to=lonlat_overlay_config["lat"]["round_to"],
        )

        # Canada map
        go_list += [
            go.Scattergl(
                x=canada_x,
                y=canada_y,
                mode="lines",
                hoverinfo="skip",
                visible=True,
                name="",
                line=dict(width=0.5, color="black"),
            )
        ]

        # need to process stations
        df = coord_prep(df, station_dv)
        ds_arr = ds[dv].values[icymin:icymax, icxmin:icxmax].copy()

        if r_or_m == "model" and mask_ctrl:
            mask = native_mask[icymin:icymax, icxmin:icxmax]
            ds_arr[~mask] = np.nan

        go_list += [
            # Interploation raster
            go.Heatmap(
                z=ds_arr,
                x=ds.rlon.values[icxmin:icxmax],
                y=ds.rlat.values[icymin:icymax],
                zmin=zmin,
                zmax=zmax,
                hoverongaps=False,
                colorscale=discrete_colorscale,
                colorbar={"tickvals": ticks},
                # showscale=False,
                visible=True,
                hovertemplate=(
                    f"<b>{design_value_id_ctrl} (Interp.): %{{z}} </b><br>"
                ),
                name="",
            ),
            # Station plot
            go.Scattergl(
                x=df.rlon,
                y=df.rlat,
                text=df[station_dv],
                mode="markers",
                marker=dict(
                    size=10,
                    symbol="circle",
                    color=df[station_dv],
                    cmin=zmin,
                    cmax=zmax,
                    line=dict(width=1, color="DarkSlateGrey"),
                    showscale=False,
                    colorscale=discrete_colorscale,
                    colorbar={"tickvals": ticks},
                ),
                hovertemplate=(
                    f"<b>{design_value_id_ctrl} (Station): "
                    f"%{{text}}</b><br>"
                ),
                visible=stations_ctrl,
                name="",
            ),
        ]

        units = ds[dv].attrs["units"]
        fig = {
            "data": go_list,
            "layout": {
                "title": (
                    f"<b>{design_value_id_ctrl} "
                    f"[{config['dvs'][design_value_id_ctrl]['description']}] "
                    f"({units})</b>"
                ),
                "font": dict(size=13, color="grey"),
                "xaxis": dict(
                    zeroline=False,
                    range=[ds.rlon.values[icxmin], ds.rlon.values[icxmax]],
                    showgrid=False,  # thin lines in the background
                    visible=False,  # numbers below
                ),
                "yaxis": dict(
                    zeroline=False,
                    range=[ds.rlat.values[icymin], ds.rlat.values[icymax]],
                    showgrid=False,  # thin lines in the background
                    visible=False,
                ),
                "xaxis_showgrid": False,
                "yaxis_showgrid": False,
                "hoverlabel": dict(
                    bgcolor="white", font_size=16, font_family="Rockwell"
                ),
                "hoverdistance": 5,
                "hovermode": "closest",
                # "width": 1000,
                "height": 750,
                "showlegend": False,
                "legend_orientation": "v",
                "scrollZoom": True,
                "uirevision": "None",
            },
        }

        return fig
