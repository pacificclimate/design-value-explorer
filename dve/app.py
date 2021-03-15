import json
import yaml

import dve
import dve.app_.map_figure
import dve.app_.table_c2
import dve.app_.colour_scale
import dve.data
import dve.layout

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np

from .data import get_data
from .map_utils import (
    pointer_rlonlat,
    rlonlat_to_rindices,
    pointer_rindices,
    rindices_to_lonlat,
    pointer_value,
)
from .download_utils import (
    download_filename,
    download_filepath,
    download_base_url,
    download_url,
)

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

    app = get_app(config)

    return app


def get_app(config):
    warnings.filterwarnings("ignore")

    # initialize app
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = "Pacific Climate Impacts Consortium Design Value Explorer"
    app.config.suppress_callback_exceptions = True

    app.layout = dve.layout.main(config)

    dve.app_.table_c2.add_callbacks(app, config)

    dve.app_.colour_scale.add_callbacks(app, config)

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
        data = get_data(config, name, interpolation)
        (dv_var_name,) = data.data_vars
        ix, iy = rlonlat_to_rindices(data, rlon, rlat)
        return data[dv_var_name].values[iy, ix]

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

        dataset = get_data(config, design_value_id_ctrl, interpolation_ctrl)
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
            # dv_table(
            #     rlon,
            #     rlat,
            #     selected_dv=design_value_id_ctrl,
            #     selected_interp=interpolation_ctrl,
            # ),
        ]

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

        dataset = get_data(config, design_value_id_ctrl, interpolation_ctrl)
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        return [
            html.A(
                "Download this data",
                href=download_url(lon, lat),
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

        dataset = get_data(config, design_value_id_ctrl, interpolation_ctrl)
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        # Create data table for download
        with open(
            os.path.join("/", download_filepath(lon, lat)),
            "w"
        ) as file:
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

    dve.app_.map_figure.add_callbacks(app, config)

    @app.server.route(f"{str(download_base_url())}/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join("/downloads/by-location"), filename
        )

    return app
