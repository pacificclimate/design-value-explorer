import json
import yaml

from climpyrical.data import read_data
from climpyrical.gridding import (
    flatten_coords,
    transform_coords,
    find_nearest_index,
)
from climpyrical.mask import stratify_coords
from climpyrical.cmd.find_matched_model_vals import add_model_values
from dve.colorbar import (
    get_cmap_divisions,
    matplotlib_to_plotly,
    plotly_discrete_colorscale,
)

from dve.data import load_data
import dve
import dve.data
import dve.layout
from dve.processing import coord_prep
from dve.generate_iso_lines import lonlat_overlay

import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import numpy as np
import matplotlib.cm
import geopandas as gpd
from pkg_resources import resource_filename

from .math_utils import sigfigs
from .map_utils import (
    pointer_rlonlat,
    rlonlat_to_rindices,
    pointer_rindices,
    rindices_to_lonlat,
    pointer_value,
)
from .download_utils import download_filename, download_filepath

import flask
import os
import warnings
import logging
import csv


logger = logging.getLogger("dve")


# TODO: This "app factory" needs to be refactored.

def make_app(config_filepath="config.yml"):
    logger.debug("Loading configuration")
    with open(config_filepath, "r") as config_file:
        config = yaml.load(config_file)
    logger.debug(f"Configuration loaded. {config}")

    data = load_data(config)

    app = get_app(config, data)

    return app


def get_app(config, data):
    warnings.filterwarnings("ignore")

    # load polygon data
    canada = gpd.read_file(
        resource_filename("dve", config["paths"]["canada_vector"])
    ).geometry
    X, Y = stratify_coords(canada)

    native_mask = (
        read_data(resource_filename("dve", config["paths"]["native_mask"]))[
            "sftlf"
        ]
        >= 1.0
    )

    # initialize app
    TIMEOUT = 60
    server = flask.Flask("app")
    app = dash.Dash("app", server=server)
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = "Pacific Climate Impacts Consortium Design Value Explorer"
    app.config.suppress_callback_exceptions = True

    app.layout = dve.layout.main(config, data)

    @app.callback(
        Output("table", "children"), [Input("design-value-id-ctrl", "value")]
    )
    def update_tablec2(value):
        df = data[value]["table"]
        df = df[["Location", "lon", "lat", data[value]["station_dv"]]].round(3)

        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            style_cell={
                "textAlign": "center",
                "whiteSpace": "normal",
                "height": "auto",
                "padding": "5px",
            },
            style_as_list_view=True,
            style_header={"backgroundColor": "white", "fontWeight": "bold"},
            data=df.to_dict("records"),
        )

    @app.callback(
        Output("colour-map-ctrl", "value"),
        [Input("design-value-id-ctrl", "value")],
    )
    def update_colour_map_ctrl_value(design_value_id):
        return config["dvs"][design_value_id]["colour_map"]

    @app.callback(
        Output("scale-ctrl", "value"), [Input("design-value-id-ctrl", "value")]
    )
    def update_scale_ctrl_value(design_value_id):
        return config["dvs"][design_value_id]["scale"]["default"]

    @app.callback(
        Output("scale-ctrl", "options"),
        [Input("design-value-id-ctrl", "value")],
    )
    def update_scale_ctrl_options(design_value_id):
        options = [
            {
                **option,
                "disabled": (
                    option["value"] == "logarithmic"
                    and config["dvs"][design_value_id]["scale"].get(
                        "disable_logarithmic", False
                    )
                ),
            }
            for option in dve.layout.scale_ctrl_options
        ]
        return options

    @app.callback(
        Output("range-slider-output-container", "children"),
        [Input("range-slider", "value")],
    )
    def update_range(value):
        return f"Range: {sigfigs(value[0])} to {sigfigs(value[1])}"

    @app.callback(
        [
            Output(component_id="range-slider", component_property="min"),
            Output(component_id="range-slider", component_property="max"),
            Output(component_id="range-slider", component_property="step"),
            Output(component_id="range-slider", component_property="value"),
        ],
        [
            Input(
                component_id="design-value-id-ctrl", component_property="value"
            ),
            Input(component_id="cbar-slider", component_property="value"),
        ],
    )
    def update_slider(value, N):
        field = data[value]["reconstruction"][data[value]["dv"]].values
        minimum = np.round(np.nanmin(field), 3)
        maximum = np.round(np.nanmax(field), 3)
        step = (maximum - minimum) / (N + 1)
        default = [minimum, maximum]
        return minimum, maximum, step, default

    # TODO: Remove when no longer needed for development
    # @app.callback(
    #     Output("hover-data", "children"),
    #     [Input("my-graph", "hoverData")]
    # )
    # def display_hover_data(hover_data):
    #     return json.dumps(hover_data, indent=2)

    def value_table(*items):
        return dbc.Table(
            [
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Th(name, style={"width": "5em"}),
                                html.Td(value),
                            ]
                        )
                        for name, value in items
                    ]
                )
            ],
            bordered=True,
            size="sm",
        )

    def dv_value(name, interpolation, rlon, rlat):
        var_name = data[name]["dv"]
        dataset = data[name][interpolation]
        ix, iy = rlonlat_to_rindices(dataset, rlon, rlat)
        # print(f"ix={ix}, iy={iy}, var_name={var_name},")
        # print(f"data[name] {data[name]}")
        return dataset[var_name].values[iy, ix]

    def dv_table(rlon, rlat, selected_dv=None, selected_interp=None):
        """
        Return a table listing values of design values at a location specified
        by rotated coordinates rlon, rlat

        :param rlon:
        :param rlat:
        :return:
        """
        return dbc.Table(
            [
                html.Thead(
                    [
                        html.Tr(
                            [
                                html.Th("DV"),
                                html.Th("Model"),
                                html.Th("Reconstruction"),
                            ]
                        )
                    ]
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [html.Th(name, style={"width": "5em"})]
                            + [
                                html.Td(
                                    round(
                                        float(
                                            dv_value(name, interp, rlon, rlat)
                                        ),
                                        3,
                                    ),
                                    style={
                                        "color": "red"
                                        if name == selected_dv
                                        and interp == selected_interp
                                        else "inherit"
                                    },
                                )
                                for interp in ("model", "reconstruction")
                            ]
                        )
                        for name in config["dvs"].keys()
                    ]
                ),
            ],
            bordered=True,
            size="sm",
        )

    @app.callback(
        Output("hover-info", "children"),
        [
            Input("my-graph", "hoverData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ],
    )
    def display_hover_info(
        hover_data, design_value_id_ctrl, interpolation_ctrl
    ):
        # TODO: Can we use a fixed value ("model" or "reconstruction") instead
        #  of interpolation_ctrl? Note: Each type of dataset has a different
        #  lat-lon grid.

        # TODO: DRY this up with respect to display_click_info when we have
        #   settled interface.

        if hover_data is None:
            return None

        dataset = data[design_value_id_ctrl][interpolation_ctrl]
        rlon, rlat = pointer_rlonlat(hover_data)
        ix, iy = pointer_rindices(hover_data, dataset)
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(hover_data)

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            ),
            dv_table(
                rlon,
                rlat,
                selected_dv=design_value_id_ctrl,
                selected_interp=interpolation_ctrl,
            ),
        ]

    # TODO: Remove when no longer needed for development
    # @app.callback(
    #     Output("click-data", "children"),
    #     [Input("my-graph", "clickData")]
    # )
    # def display_click_data(click_data):
    #     return json.dumps(click_data, indent=2)

    # TODO: This can be better done by setting the "href" and "download"
    #   properties on a static download link established in layout.py.
    @app.callback(
        Output("data-download-header", "children"),
        [
            Input("my-graph", "clickData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ],
    )
    def display_download_button(
        click_data, design_value_id_ctrl, interpolation_ctrl
    ):
        """
        To get the layout we want, we have to break the map-click callback into
        two parts: Download button and data display. Unfortunately this is
        repetitive but no other solution is known.
        """
        if click_data is None:
            return None

        dataset = data[design_value_id_ctrl][interpolation_ctrl]
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        return [
            html.A(
                "Download this data",
                href=download_filepath(lon, lat),
                download=download_filename(lon, lat),
                className="btn btn-primary btn-sm mb-1",
            )
        ]

    @app.callback(
        Output("click-info", "children"),
        [
            Input("my-graph", "clickData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ],
    )
    def display_click_info(
        click_data, design_value_id_ctrl, interpolation_ctrl
    ):
        """
        To get the layout we want, we have to break the map-click callback into
        two parts: Download button and data display. Unfortunately this is
        repetitive but no other solution is known.
        """
        # TODO: Can we use a fixed value ("model" or "reconstruction" instead
        #  of interp_ctrl? ... The grids for each are different and
        #  give different values for lat/lon at the same pointer locn.
        # TODO: DRY
        if click_data is None:
            return None

        dataset = data[design_value_id_ctrl][interpolation_ctrl]
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        # Create data table for download
        with open(download_filepath(lon, lat), "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(("Latitude", lat))
            writer.writerow(("Longitude", lon))
            writer.writerow(tuple())
            writer.writerow(
                ("Design Value ID", "Model Value", "Reconstruction Value")
            )
            for dv_id in config["dvs"].keys():
                writer.writerow(
                    (
                        dv_id,
                        float(dv_value(dv_id, "model", rlon, rlat)),
                        float(dv_value(dv_id, "reconstruction", rlon, rlat)),
                    )
                )

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            ),
            dv_table(
                rlon,
                rlat,
                selected_dv=design_value_id_ctrl,
                selected_interp=interpolation_ctrl,
            ),
        ]

    # TODO: What is this for? Remove?
    ds = data[list(data.keys())[0]]["reconstruction"]

    viewport = None

    @app.callback(
        Output("my-graph", "figure"),
        [
            Input("mask-ctrl", "on"),
            Input("stations-ctrl", "on"),
            Input("design-value-id-ctrl", "value"),
            Input("cbar-slider", "value"),
            Input("range-slider", "value"),
            Input("dataset-ctrl", "value"),
            Input("scale-ctrl", "value"),
            Input("colour-map-ctrl", "value"),
            Input("my-graph", "relayoutData"),
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
        relayout_data,
    ):
        # Save viewport bounds when it changes (zoom, pan events)
        nonlocal viewport
        if relayout_data is not None and "xaxis.range[0]" in relayout_data:
            viewport = {
                "x_min": relayout_data["xaxis.range[0]"],
                "x_max": relayout_data["xaxis.range[1]"],
                "y_min": relayout_data["yaxis.range[0]"],
                "y_max": relayout_data["yaxis.range[1]"],
            }

        zmin = range_slider[0]
        zmax = range_slider[1]

        if scale_ctrl == "logarithmic":
            # TODO: Remove z_offset stuff. Defunct.
            z_offset = config["dvs"][design_value_id_ctrl].get("z_offset", 0)
            ticks = np.linspace(
                np.log10(zmin + z_offset),
                np.log10(zmax + z_offset),
                cbar_slider + 1,
            )
            ticks = np.around(10 ** (ticks) - z_offset, 2)
        else:
            ticks = np.around(np.linspace(zmin, zmax, cbar_slider + 1), 3)

        cmap = matplotlib.cm.get_cmap(colour_map_ctrl, cbar_slider)

        colours = [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]

        discrete_colorscale = plotly_discrete_colorscale(ticks, colours)

        r_or_m = dataset_ctrl

        dv = data[design_value_id_ctrl]["dv"]
        station_dv = data[design_value_id_ctrl]["station_dv"]
        ds = data[design_value_id_ctrl][r_or_m]
        df = data[design_value_id_ctrl]["stations"]

        # TODO: This is recalculated for every update, but X and Y don't change
        #   once set. Factor out.
        x1 = min(value for value in X if value is not None)
        x2 = max(value for value in X if value is not None)
        y1 = min(value for value in Y if value is not None)
        y2 = max(value for value in Y if value is not None)

        ixmin = find_nearest_index(ds.rlon.values, np.nanmin(x1))
        ixmax = find_nearest_index(ds.rlon.values, np.nanmax(x2))
        iymin = find_nearest_index(ds.rlat.values, np.nanmin(y1))
        iymax = find_nearest_index(ds.rlat.values, np.nanmax(y2))

        go_list = []

        # Lon-lat overlay
        go_list += lonlat_overlay(
            # It's not clear why the grid sizes should be taken from the
            # dataset, but that's how the code works. Ick.
            rlon_grid_size=ds.rlon.size,
            rlat_grid_size=ds.rlat.size,
            viewport=viewport,
            num_lon_intervals=config["map"]["grid"]["lon"]["num_intervals"],
            lon_round_to=config["map"]["grid"]["lon"]["round_to"],
            num_lat_intervals=config["map"]["grid"]["lat"]["num_intervals"],
            lat_round_to=config["map"]["grid"]["lat"]["round_to"],
        )

        # Canada map
        go_list += [
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

        # need to process stations
        df = coord_prep(df, station_dv)
        ds_arr = ds[dv].values[iymin:iymax, ixmin:ixmax].copy()

        if r_or_m == "model" and mask_ctrl:
            mask = native_mask[iymin:iymax, ixmin:ixmax]
            ds_arr[~mask] = np.nan

        go_list += [
            # Interploation raster
            go.Heatmap(
                z=ds_arr,
                x=ds.rlon.values[ixmin:ixmax],
                y=ds.rlat.values[iymin:iymax],
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
                    range=[ds.rlon.values[ixmin], ds.rlon.values[ixmax]],
                    showgrid=False,  # thin lines in the background
                    visible=False,  # numbers below
                ),
                "yaxis": dict(
                    zeroline=False,
                    range=[ds.rlat.values[iymin], ds.rlat.values[iymax]],
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

    @app.server.route("/downloads/by-location/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join("/downloads/by-location"), filename
        )

    return app
