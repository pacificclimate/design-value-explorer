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


def add(app, config):
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
            # DV selection
            Input("design-value-id-ctrl", "value"),
            # Overlay options
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
            Input("mask-ctrl", "on"),
            Input("stations-ctrl", "on"),
            # Colour scale options
            Input("colour-map-ctrl", "value"),
            Input("scale-ctrl", "value"),
            Input("cbar-slider", "value"),
            Input("colourbar-range-ctrl", "value"),
            # Client-side state
            Input("viewport-ds", "children"),
        ],
    )
    def update_ds(
        # DV selection
        design_value_id,
        # Overlay options
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        mask_on,
        show_stations,
        # Colour scale options
        colour_map_name,
        scale,
        num_colours,
        data_range,
        # Client-side state
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
        if data_range is None:
            logger.debug("### update_ds: range_slider is None")
            return empty_fig

        viewport = viewport_ds and json.loads(viewport_ds)

        zmin = data_range[0]
        zmax = data_range[1]

        if scale == "logarithmic":
            ticks = np.linspace(np.log10(zmin), np.log10(zmax), num_colours + 1)
            ticks = np.around(10 ** (ticks), 2)
        else:
            ticks = np.around(np.linspace(zmin, zmax, num_colours + 1), 3)

        cmap = matplotlib.cm.get_cmap(colour_map_name, num_colours)

        colours = [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]

        discrete_colorscale = plotly_discrete_colorscale(ticks, colours)

        # TODO: Rename all this shit
        ds = get_data(config, design_value_id, climate_regime,
                      historical_dataset_id, future_dataset_id)
        (dv,) = ds.data_vars  # TODO: Rename dv_var_name
        # TODO: Don't display stations when climate_regime != "historical"?
        df = get_data(config, design_value_id, "historical", historical_dataset_id="stations")
        station_dv = config["dvs"][design_value_id]["station_dv"]

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

        if historical_dataset_id == "model" and mask_on:
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
                    f"<b>{design_value_id} (Interp.): %{{z}} </b><br>"
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
                    f"<b>{design_value_id} (Station): "
                    f"%{{text}}</b><br>"
                ),
                visible=show_stations,
                name="",
            ),
        ]

        units = ds[dv].attrs["units"]
        fig = {
            "data": go_list,
            "layout": {
                "title": (
                    f"<b>{design_value_id} "
                    f"[{config['dvs'][design_value_id]['description']}] "
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

    @app.callback(
        Output("viewport-ds", "children"),
        [Input("my-graph", "relayoutData")],
        [State("viewport-ds", "children")],
    )
    def update_viewport(relayout_data, prev_viewport):
        # Save map viewport bounds when and only when they change
        # (zoom, pan events)
        if relayout_data is not None and "xaxis.range[0]" in relayout_data:
            viewport = {
                "x_min": relayout_data["xaxis.range[0]"],
                "x_max": relayout_data["xaxis.range[1]"],
                "y_min": relayout_data["yaxis.range[0]"],
                "y_max": relayout_data["yaxis.range[1]"],
            }
            return json.dumps(viewport)
        return prev_viewport
