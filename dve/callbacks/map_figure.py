import json
import logging
from pkg_resources import resource_filename
import math

import dash
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

import geopandas as gpd

from dve.config import (
    dv_has_climate_regime,
    dv_roundto,
    dv_units,
    map_title,
    dv_historical_stations_column,
    dv_colour_bar_sigfigs,
    dv_name,
    file_exists,
    filepath_for,
)
from dve.data import get_data_object
from dve.colorbar import (
    discrete_colorscale,
    colorscale_colors,
    discrete_colorscale_colorbar,
    use_ticks,
    uniformly_spaced_with_target,
)
from dve.generate_iso_lines import lonlat_overlay
from dve.config import dv_label
from dve.processing import coord_prep
from dve.math_utils import round_to_multiple, sigfigs
from dve.timing import timing

from climpyrical.gridding import find_nearest_index
from climpyrical.mask import stratify_coords


logger = logging.getLogger(__name__)
timing_log_info = logger.info
timing_log_debug = logger.debug  # Set to None to not log debug timing

lang = "en"  # TODO: Replace with language selection


def message_figure(message):
    """Return a figure containing only a text message"""
    return go.Figure(
        layout=go.Layout(
            xaxis=go.layout.XAxis(visible=False),
            yaxis=go.layout.YAxis(visible=False),
            annotations=[
                go.layout.Annotation(
                    text=message,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=go.layout.annotation.Font(size=16),
                )
            ],
        )
    )


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

    @app.callback(
        Output("map_main_graph", "figure"),
        # Tab selection
        Input("main_tabs", "active_tab"),
        # DV selection
        Input("design_variable", "value"),
        # Overlay options
        Input("climate_regime", "value"),
        # Input("historical_dataset_id", "value"),
        Input("future_dataset_id", "value"),
        Input("show_stations", "on"),
        Input("show_grid", "on"),
        # Colour scale options
        Input("color_map", "value"),
        Input("color_scale_type", "value"),
        Input("num_colors", "value"),
        Input("color_scale_data_range", "value"),
        # Client-side state
        Input("viewport-ds", "children"),
    )
    def update_map(
        # Tab selection
        main_tabs_active_tab,
        # DV selection
        design_variable,
        # Overlay options
        climate_regime,
        future_dataset_id,
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
        with timing("Update map", log=timing_log_info):
            # Do not update if the tab is not selected
            if main_tabs_active_tab != "map-tab":
                return dash.no_update

            historical_dataset_id = "reconstruction"

            ctx = dash.callback_context

            viewport = viewport_ds and json.loads(viewport_ds)

            if ctx.triggered and ctx.triggered[0]["prop_id"].startswith(
                "viewport-ds"
            ):
                # Do not update if viewport has changed but lat-lon grid is not
                # shown. Changing lat-lon grid for vp change is only reason to
                # update.
                if not show_grid:
                    return dash.no_update

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
                        return dash.no_update

            raster_filepath = filepath_for(
                config,
                design_variable,
                climate_regime,
                historical_dataset_id,
                future_dataset_id,
            )

            # Show info message if design values for requested climate regime do not
            # exist.
            if raster_filepath is None:
                what = {
                    "historical": "historical values",
                    "future": "future projections",
                }[climate_regime]
                return message_figure(
                    f"No {what} are available for "
                    f"{dv_name(config, lang, design_variable)} "
                    f"at this time."
                )

            # Show error message if configured data file does not exist.
            if not file_exists(raster_filepath):
                title = map_title(
                    config, lang,
                    design_variable,
                    climate_regime,
                    historical_dataset_id,
                    future_dataset_id,
                )
                return message_figure(
                    f"Error: Data is not available for <br>"
                    f"<b>{title}</b> <br><br>"
                    f"Please report this error to the "
                    f"application contact given "
                    f"in the <b>About > Contact</b> tab."
                )

            # Build the maps figure.

            # The list `maps` is the set of overlaid traces that comprise the map.
            # It is built up incrementally depending on the values of the inputs.
            maps = []

            roundto = dv_roundto(config, design_variable, climate_regime)
            if color_scale_type == "linear":
                zmin = round_to_multiple(
                    color_scale_data_range[0], roundto, "down"
                )
                zmax = round_to_multiple(
                    color_scale_data_range[1], roundto, "up"
                )
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

            # Hacky fix for logarithmic scales for data with min value zero.
            # Note that log scale is prohibited for several datasets, but is allowed
            # for a few (e.g., RL50) that can include 0.
            if color_scale_type == "logarithmic" and zmin == 0:
                zmin = zmax / config["map"]["logscale_zmin_factor"]

            boundaries = uniformly_spaced_with_target(
                zmin,
                zmax,
                num_colours + 1,
                target=target,
                scale=color_scale_type,
            )
            # logger.debug(f"boundaries = {boundaries}")
            num_actual_colors = len(boundaries) - 1
            colours = colorscale_colors(color_map_name, num_actual_colors)
            colorscale = discrete_colorscale(boundaries, colours)
            # logger.debug(f"colorscale = {colorscale}")

            logger.debug("update_ds: get raster dataset")
            raster_dataset = get_data_object(
                config,
                design_variable,
                climate_regime,
                historical_dataset_id,
                future_dataset_id,
            )
            with timing("extract vars from raster", log=timing_log_debug):
                rlon, rlat, dv = raster_dataset.apply(
                    lambda dvds, ds: (ds.rlon, ds.rlat, ds[dvds.dv_name])
                )

            # Trace: Lon-lat overlay
            if show_grid:
                lonlat_overlay_config = config["map"]["lonlat_overlay"]

                with timing("create lon-lat graticule", log=timing_log_debug):
                    maps += lonlat_overlay(
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
                        lon_min=lonlat_overlay_config["lon"]["min"],
                        lon_max=lonlat_overlay_config["lon"]["max"],
                        lat_min=lonlat_overlay_config["lat"]["min"],
                        lat_max=lonlat_overlay_config["lat"]["max"],
                    )

            # Trace: Canada map
            maps += [
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

            # Trace: Heatmap (raster)

            # Index values for clipping data to Canada bounds
            icxmin = find_nearest_index(rlon.values, cx_min)
            icxmax = find_nearest_index(rlon.values, cx_max)
            icymin = find_nearest_index(rlat.values, cy_min)
            icymax = find_nearest_index(rlat.values, cy_max)

            with timing("extract dv values from raster", log=timing_log_debug):
                ds_arr = dv.values[icymin:icymax, icxmin:icxmax].copy()
            # Experiment to characterize time to process entire raster.
            # Takes about 350 ms on workstation.
            # with timing("iterate dv values", log=timing_log):
            #     for i in range(icxmax - icxmin):
            #         for j in range(icymax - icymin):
            #             x = ds_arr[j,i]

            with timing("create heatmap", log=timing_log_debug):
                maps.append(
                    go.Heatmap(
                        z=ds_arr,
                        x=rlon.values[icxmin:icxmax],
                        y=rlat.values[icymin:icymax],
                        zmin=boundaries[0],
                        zmax=boundaries[-1],
                        hoverongaps=False,
                        colorscale=colorscale,
                        showscale=False,  # Hide colorbar
                        visible=True,
                        hovertemplate=(
                            f"<b>Interpolated {dv_label(config, lang, design_variable, climate_regime)}: %{{z}} </b><br>"
                        ),
                        name="",
                    )
                )

            # Trace: Stations
            if show_stations and dv_has_climate_regime(
                config, design_variable, "historical"
            ):
                logger.debug("update_ds: get station dataset")
                df = get_data_object(
                    config,
                    design_variable,
                    "historical",
                    historical_dataset_id="stations",
                ).data_frame()
                stations_column = dv_historical_stations_column(
                    config, design_variable
                )
                with timing("coord_prep for stations", log=timing_log_debug):
                    df = coord_prep(df, stations_column)
                maps.append(
                    go.Scattergl(
                        x=df.rlon,
                        y=df.rlat,
                        text=df[stations_column],
                        mode="markers",
                        marker=dict(
                            size=10,
                            symbol="circle",
                            color=df[stations_column],
                            cmin=zmin,
                            cmax=zmax,
                            line=dict(width=1, color="DarkSlateGrey"),
                            colorscale=colorscale,
                            showscale=False,  # Hide colorbar
                        ),
                        hovertemplate=(
                            f"<b>Station {dv_label(config, lang, design_variable, climate_regime)}: "
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
                [
                    sigfigs(
                        t,
                        dv_colour_bar_sigfigs(
                            config, design_variable, climate_regime
                        ),
                    )
                    for t in tickvals
                ],
            )

            # Create the figure that will be populated with the heatmap and colorbar
            # as subplots.
            figure = go.Figure(
                layout=go.Layout(
                    title=go.layout.Title(
                        text=map_title(
                            config, lang,
                            design_variable,
                            climate_regime,
                            historical_dataset_id,
                            future_dataset_id,
                        ),
                        **config["map"]["layout"]["title"],
                    ),
                    showlegend=False,
                    uirevision="None",
                    **config["map"]["layout"]["main"],
                )
            )
            figure.set_subplots(**config["map"]["layout"]["subplots"]["layout"])

            # Add colorbar trace to figure. Do this first so that the colourbar
            # traces have the first (3) curve numbers, as reported by the
            # `hoverData` and `clickData` properties of the map component. This
            # makes it possible to consistently respond only to hovers/clicks on
            # the map traces.
            colorbar_location = config["map"]["layout"]["subplots"]["colorbar"][
                "location"
            ]
            figure.add_trace(colorbar["trace"], **colorbar_location)
            figure.update_xaxes(colorbar["xaxis"], **colorbar_location)
            figure.update_yaxes(colorbar["yaxis"], **colorbar_location)

            # Add map traces to figure
            map_location = config["map"]["layout"]["subplots"]["maps"][
                "location"
            ]
            for m in maps:
                figure.add_trace(m, **map_location)
            figure.update_xaxes(
                go.layout.XAxis(
                    zeroline=False,
                    range=[rlon.values[icxmin], rlon.values[icxmax]],
                    showgrid=False,
                    visible=False,
                ),
                **map_location,
            )
            figure.update_yaxes(
                go.layout.YAxis(
                    zeroline=False,
                    range=[rlat.values[icymin], rlat.values[icymax]],
                    showgrid=False,
                    visible=False,
                ),
                **map_location,
            )

            return figure

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

        return dash.no_update
