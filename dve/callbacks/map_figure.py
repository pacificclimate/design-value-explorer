import json
import logging
from pkg_resources import resource_filename
import math

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

import geopandas as gpd
import numpy as np

from dve.config import dv_has_climate_regime, dv_roundto, dv_units
from dve.data import get_data
from dve.colorbar import (
    discrete_colorscale,
    colorscale_colors,
    discrete_colorscale_colorbar,
    use_ticks,
    uniformly_spaced_with_target,
    scale_transform,
)
from dve.generate_iso_lines import lonlat_overlay
from dve.config import dv_label, climate_regime_label, dataset_label
from dve.processing import coord_prep
from dve.math_utils import round_to_multiple
from dve.timing import timing

from climpyrical.data import read_data
from climpyrical.gridding import find_nearest_index
from climpyrical.mask import stratify_coords


logger = logging.getLogger("dve")
timing_log = logger.debug  # Set to None to not log timing


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
        [Output("map_main_graph", "figure"), Output("my-colorscale", "figure")],
        [
            # Tab selection
            Input("tabs", "active_tab"),
            # DV selection
            Input("design_variable", "value"),
            # Overlay options
            Input("climate_regime", "value"),
            Input("historical_dataset_id", "value"),
            Input("future_dataset_id", "value"),
            Input("apply_mask", "on"),
            Input("show_stations", "on"),
            Input("show_grid", "on"),
            # Colour scale options
            Input("color_map", "value"),
            Input("color_scale_type", "value"),
            Input("num_colors", "value"),
            Input("color_scale_data_range", "value"),
            # Client-side state
            Input("viewport-ds", "children"),
        ],
    )
    def update_map(
        # Tab selection
        active_tab,
        # DV selection
        design_variable,
        # Overlay options
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        apply_mask,
        show_stations,
        show_grid,
        # Colour scale options
        color_map_name,
        color_scale_type,
        num_colours,
        color_scale_data_range,
        # Client-side state
        viewport_ds,
    ):
        # Do not update if the tab is not selected
        if active_tab != "map-tab":
            raise PreventUpdate

        ctx = dash.callback_context

        viewport = viewport_ds and json.loads(viewport_ds)

        if ctx.triggered and ctx.triggered[0]["prop_id"].startswith(
            "viewport-ds"
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
                if math.isclose(
                    vp_prev["x_max"] - vp_prev["x_min"],
                    vp_curr["x_max"] - vp_curr["x_min"],
                ) and math.isclose(
                    vp_prev["y_max"] - vp_prev["y_min"],
                    vp_curr["y_max"] - vp_curr["y_min"],
                ):
                    raise PreventUpdate

        # Do not update if design values for requested climate regime do not
        # exist.
        if not dv_has_climate_regime(config, design_variable, climate_regime):
            raise PreventUpdate

        # This list of figures is returned by this function. It is built up
        # incrementally depending on the values of the inputs.
        figures = []

        roundto = dv_roundto(config, design_variable, climate_regime)
        if color_scale_type == "linear":
            zmin = round_to_multiple(color_scale_data_range[0], roundto, "down")
            zmax = round_to_multiple(color_scale_data_range[1], roundto, "up")
        else:
            # TODO: Round for logarithmic scale. This is not easy.
            zmin, zmax = color_scale_data_range
        logger.debug(f"color_scale_data_range = {color_scale_data_range}")
        logger.debug(f"zmin = {zmin}")
        logger.debug(f"zmax = {zmax}")

        # Create colorscale appropriate to this map
        if climate_regime == "historical":
            target = None
        else:
            is_relative = (
                dv_units(config, design_variable, climate_regime) == "ratio"
            )
            target = 1 if is_relative else 0
            target = target if (zmin <= target <= zmax) else None
        boundaries = uniformly_spaced_with_target(
            zmin, zmax, num_colours + 1, target=target, scale=color_scale_type
        )
        logger.debug(f"boundaries = {boundaries}")
        num_actual_colors = len(boundaries) - 1
        colours = colorscale_colors(color_map_name, num_actual_colors)
        colorscale = discrete_colorscale(boundaries, colours)

        logger.debug("update_ds: get raster dataset")
        raster_dataset = get_data(
            config,
            design_variable,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        with timing("extract vars from raster", log=timing_log):
            rlon, rlat, dv = raster_dataset.apply(
                lambda dvds, ds: (ds.rlon, ds.rlat, ds[dvds.dv_name])
            )

        # Figure: Lon-lat overlay
        if show_grid:
            lonlat_overlay_config = config["map"]["lonlat_overlay"]

            with timing("create lon-lat graticule", log=timing_log):
                figures += lonlat_overlay(
                    # It's not clear why the grid sizes should be taken from the
                    # dataset, but that's how the code works. Ick.
                    rlon_grid_size=rlon.size,
                    rlat_grid_size=rlat.size,
                    viewport=viewport and viewport["current"],
                    num_lon_intervals=lonlat_overlay_config["lon"][
                        "num_intervals"
                    ],
                    lon_round_to=lonlat_overlay_config["lon"]["round_to"],
                    num_lat_intervals=lonlat_overlay_config["lat"][
                        "num_intervals"
                    ],
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

        with timing("extract dv values from raster", log=timing_log):
            ds_arr = dv.values[icymin:icymax, icxmin:icxmax].copy()
        # Experiment to characterize time to process entire raster.
        # Takes about 350 ms on workstation.
        # with timing("iterate dv values", log=timing_log):
        #     for i in range(icxmax - icxmin):
        #         for j in range(icymax - icymin):
        #             x = ds_arr[j,i]

        if historical_dataset_id == "model" and apply_mask:
            with timing("apply masking to dataset", log=timing_log):
                mask = native_mask[icymin:icymax, icxmin:icxmax]
                ds_arr[~mask] = np.nan

        with timing("create heatmap", log=timing_log):
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
                        f"<b>Interpolated {dv_label(config, design_variable, climate_regime)}: %{{z}} </b><br>"
                    ),
                    name="",
                )
            )

        # Figure: Stations
        if show_stations and dv_has_climate_regime(
            config, design_variable, "historical"
        ):
            logger.debug("update_ds: get station dataset")
            df = get_data(
                config,
                design_variable,
                "historical",
                historical_dataset_id="stations",
            ).data_frame()
            station_dv = config["dvs"][design_variable]["station_dv"]
            with timing("coord_prep for stations", log=timing_log):
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
                        f"<b>Station {dv_label(config, design_variable, climate_regime)}: "
                        f"%{{text}}</b><br>"
                    ),
                    name="",
                )
            )

        # Accompanying colorbar. It would be nice to use the built-in colorbar,
        # but Plotly's logarithmic colorbar is not suitable to our purposes.
        tickvals = use_ticks(
            zmin,
            zmax,
            target,
            color_scale_type,
            num_actual_colors,
            config["ui"]["ticks"]["max-num"],
        )
        colorbar = discrete_colorscale_colorbar(
            boundaries,
            colorscale,
            color_scale_type,
            tickvals,
            [round_to_multiple(t, roundto) for t in tickvals],
        )

        return (
            {
                "data": figures,
                "layout": {
                    "title": (
                        config["ui"]["labels"]["map"]["title"].format(
                            dv=dv_label(
                                config,
                                design_variable,
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
        [Input("map_main_graph", "relayoutData")],
        [State("viewport-ds", "children")],
    )
    def update_viewport(map_main_relayout_data, prev_viewport):
        # Save map viewport bounds when and only when they change
        # (zoom, pan events)
        prev_viewport = json.loads(prev_viewport)
        if map_main_relayout_data is not None:
            if "xaxis.autorange" in map_main_relayout_data:
                return json.dumps(None)

            if "xaxis.range[0]" in map_main_relayout_data:
                x_min = map_main_relayout_data["xaxis.range[0]"]
                x_max = map_main_relayout_data["xaxis.range[1]"]
                y_min = map_main_relayout_data["yaxis.range[0]"]
                y_max = map_main_relayout_data["yaxis.range[1]"]
                viewport = {
                    "current": {
                        "x_min": x_min,
                        "x_max": x_max,
                        "y_min": y_min,
                        "y_max": y_max,
                    },
                    "previous": prev_viewport and prev_viewport["current"],
                }
                return json.dumps(viewport)

        raise PreventUpdate
