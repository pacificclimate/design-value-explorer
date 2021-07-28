import json
import logging
from pkg_resources import resource_filename
import math

import dash
from dash.dependencies import Input, Output, State
from dve.config import dv_has_climate_regime
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

import geopandas as gpd
import numpy as np

from dve.data import get_data
from dve.colorbar import (
    uniformly_spaced,
    discrete_colorscale,
    colorscale_colors,
    discrete_colorscale_colorbar,
    use_ticks,
)
from dve.generate_iso_lines import lonlat_overlay
from dve.config import dv_label, climate_regime_label, dataset_label
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
        [Output("my-graph", "figure"), Output("my-colorscale", "figure")],
        [
            # DV selection
            Input("design-value-id-ctrl", "value"),
            # Overlay options
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
            Input("mask-ctrl", "on"),
            Input("stations-ctrl", "on"),
            Input("grid-ctrl", "on"),
            # Colour scale options
            Input("colour-map-ctrl", "value"),
            Input("scale-ctrl", "value"),
            Input("cbar-slider", "value"),
            Input("colourbar-range-ctrl", "value"),
            # Client-side state
            Input("viewport-ds", "children"),
        ],
    )
    def update_map(
        # DV selection
        design_value_id,
        # Overlay options
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        mask_on,
        show_stations,
        show_grid,
        # Colour scale options
        colour_map_name,
        scale,
        num_colours,
        data_range,
        # Client-side state
        viewport_ds,
    ):
        ctx = dash.callback_context

        viewport = viewport_ds and json.loads(viewport_ds)

        if (
            ctx.triggered
            and ctx.triggered[0]["prop_id"].startswith("viewport-ds")
        ):
            # Do not update if viewport has changed but lat-lon grid is not shown.
            # Changing lat-lon grid for vp change is only reason to update.
            if not show_grid:
                raise PreventUpdate

            # Do not update if viewport dimensions have not changed.
            # Grid covers entirety of Canada, and only changes when vp dims
            # change.
            if viewport and viewport["previous"]:
                vp_prev = viewport["previous"]
                vp_curr = viewport["current"]
                if (
                    math.isclose(
                        vp_prev["x_max"] - vp_prev["x_min"],
                        vp_curr["x_max"] - vp_curr["x_min"],
                    )
                    and math.isclose(
                        vp_prev["y_max"] - vp_prev["y_min"],
                        vp_curr["y_max"] - vp_curr["y_min"],
                    )
                ):
                    raise PreventUpdate

        # Do not update if design values for requested climate regime do not
        # exist.
        if not dv_has_climate_regime(config, design_value_id, climate_regime):
            raise PreventUpdate

        # This list of figures is returned by this function. It is built up
        # incrementally depending on the values of the inputs.
        figures = []

        zmin = data_range[0]
        zmax = data_range[1]

        boundaries = uniformly_spaced(zmin, zmax, num_colours + 1, scale)
        colours = colorscale_colors(colour_map_name, num_colours)
        colorscale = discrete_colorscale(boundaries, colours)

        logger.debug("update_ds: get raster dataset")
        raster_dataset = get_data(
            config,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        rlon, rlat, dv = raster_dataset.apply(
            lambda dvds, ds: (ds.rlon, ds.rlat, ds[dvds.dv_name])
        )

        # Figure: Lon-lat overlay
        if show_grid:
            lonlat_overlay_config = config["map"]["lonlat_overlay"]
            figures += lonlat_overlay(
                # It's not clear why the grid sizes should be taken from the
                # dataset, but that's how the code works. Ick.
                rlon_grid_size=rlon.size,
                rlat_grid_size=rlat.size,
                viewport=viewport and viewport["current"],
                num_lon_intervals=lonlat_overlay_config["lon"]["num_intervals"],
                lon_round_to=lonlat_overlay_config["lon"]["round_to"],
                num_lat_intervals=lonlat_overlay_config["lat"]["num_intervals"],
                lat_round_to=lonlat_overlay_config["lat"]["round_to"],
            )

        # Figure: Canada map
        figures += [
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

        # Figure: Heatmap (raster)

        # Index values for clipping data to Canada bounds
        icxmin = find_nearest_index(rlon.values, cx_min)
        icxmax = find_nearest_index(rlon.values, cx_max)
        icymin = find_nearest_index(rlat.values, cy_min)
        icymax = find_nearest_index(rlat.values, cy_max)

        ds_arr = dv.values[icymin:icymax, icxmin:icxmax]

        if historical_dataset_id == "model" and mask_on:
            mask = native_mask[icymin:icymax, icxmin:icxmax]
            ds_arr[~mask] = np.nan

        figures.append(
            go.Heatmap(
                z=ds_arr,
                x=rlon.values[icxmin:icxmax],
                y=rlat.values[icymin:icymax],
                zmin=zmin,
                zmax=zmax,
                hoverongaps=False,
                colorscale=colorscale,
                showscale=False,  # Hide colorbar
                visible=True,
                hovertemplate=(
                    f"<b>Interpolated {dv_label(config, design_value_id, climate_regime)}: %{{z}} </b><br>"
                ),
                name="",
            )
        )

        # Figure: Stations
        if dv_has_climate_regime(config, design_value_id, "historical"):
            logger.debug("update_ds: get station dataset")
            df = get_data(
                config,
                design_value_id,
                "historical",
                historical_dataset_id="stations",
            ).data_frame()
            station_dv = config["dvs"][design_value_id]["station_dv"]
            df = coord_prep(df, station_dv)
            figures.append(
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
                        colorscale=colorscale,
                        showscale=False,  # Hide colorbar
                    ),
                    hovertemplate=(
                        f"<b>Station {dv_label(config, design_value_id, climate_regime)}: "
                        f"%{{text}}</b><br>"
                    ),
                    visible=show_stations,
                    name="",
                )
            )

        # Accompanying colorbar. It would be nice to use the built-in colorbar,
        # but Plotly's logarithmic colorbar is not suitable to our purposes.
        tickvals = use_ticks(
            zmin, zmax, scale, num_colours, config["ui"]["ticks"]["max-num"]
        )
        colorbar = discrete_colorscale_colorbar(
            boundaries, colorscale, scale, tickvals, np.around(tickvals, 2)
        )

        return (
            {
                "data": figures,
                "layout": {
                    "title": (
                        config["ui"]["labels"]["map"]["title"].format(
                            dv=dv_label(
                                config,
                                design_value_id,
                                climate_regime,
                                with_description=True,
                            ),
                            climate_regime=climate_regime_label(
                                config, climate_regime, which="short"
                            ),
                            dataset=dataset_label(
                                config,
                                climate_regime,
                                historical_dataset_id,
                                future_dataset_id,
                                which="short",
                                nice=True,
                            ),
                        )
                    ),
                    "font": dict(size=13, color="grey"),
                    "xaxis": dict(
                        zeroline=False,
                        range=[rlon.values[icxmin], rlon.values[icxmax]],
                        showgrid=False,  # thin lines in the background
                        visible=False,  # numbers below
                    ),
                    "yaxis": dict(
                        zeroline=False,
                        range=[rlat.values[icymin], rlat.values[icymax]],
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
                    # width is unspecified; it is therefore adaptive to window
                    "height": 750,
                    "showlegend": False,
                    "legend_orientation": "v",
                    "scrollZoom": True,
                    "uirevision": "None",
                },
            },
            colorbar,
        )

    @app.callback(
        Output("viewport-ds", "children"),
        [Input("my-graph", "relayoutData")],
        [State("viewport-ds", "children")],
    )
    def update_viewport(relayout_data, prev_viewport):
        # Save map viewport bounds when and only when they change
        # (zoom, pan events)
        prev_viewport = json.loads(prev_viewport)
        if relayout_data is not None:
            if "xaxis.autorange" in relayout_data:
                return json.dumps(None)

            if "xaxis.range[0]" in relayout_data:
                x_min = relayout_data["xaxis.range[0]"]
                x_max = relayout_data["xaxis.range[1]"]
                y_min = relayout_data["yaxis.range[0]"]
                y_max = relayout_data["yaxis.range[1]"]
                viewport = {
                    "current": {
                        "x_min": x_min,
                        "x_max": x_max,
                        "y_min": y_min,
                        "y_max": y_max,
                    },
                    "previous": prev_viewport and prev_viewport["current"]
                }
                return json.dumps(viewport)

        raise PreventUpdate
