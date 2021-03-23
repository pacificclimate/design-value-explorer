import json
import logging
from pkg_resources import resource_filename

from dash.dependencies import Input, Output, State
from dve.config import dv_has_climate_regime
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

import geopandas as gpd
import matplotlib.cm
import numpy as np

from dve.data import get_data
from dve.colorbar import plotly_discrete_colorscale
from dve.generate_iso_lines import lonlat_overlay
from dve.labelling_utils import dv_label
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
        if not dv_has_climate_regime(
            config, design_value_id, climate_regime
        ):
            raise PreventUpdate

        # This list of figures is returned by this function. It is built up
        # incrementally depending on the values of the inputs.
        figures = []

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

        logger.debug("update_ds: get raster dataset")
        raster_dataset = get_data(
            config,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        rlon, rlat, dv = raster_dataset.apply(
            lambda dvds, ds: (
                ds.rlon,
                ds.rlat,
                ds[dvds.dv_name],
            )
        )

        # Figure: Lon-lat overlay
        lonlat_overlay_config = config["map"]["lonlat_overlay"]
        figures += lonlat_overlay(
            # It's not clear why the grid sizes should be taken from the
            # dataset, but that's how the code works. Ick.
            rlon_grid_size=rlon.size,
            rlat_grid_size=rlat.size,
            viewport=viewport,
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

        # TODO: Why copy?
        ds_arr = dv.values[icymin:icymax, icxmin:icxmax].copy()

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
                colorscale=discrete_colorscale,
                colorbar={"tickvals": ticks},
                # showscale=False,
                visible=True,
                hovertemplate=(
                    f"<b>{design_value_id} (Interp.): %{{z}} </b><br>"
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
                        showscale=False,
                        colorscale=discrete_colorscale,
                        colorbar={"tickvals": ticks},
                    ),
                    hovertemplate=(
                        f"<b>{design_value_id} (Station): " f"%{{text}}</b><br>"
                    ),
                    visible=show_stations,
                    name="",
                )
            )

        return {
            "data": figures,
            "layout": {
                "title": (
                    f"{dv_label(config, design_value_id, climate_regime, with_description=True, )} "
                    f"     {config['ui']['labels']['climate_regime'][climate_regime]}"
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
        }

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
