import json
import yaml

import dve
import dve.app_.map_figure
import dve.data
import dve.layout

import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np

from .data import get_data
from .math_utils import sigfigs
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

    @app.callback(
        [Output("table-C2-dv", "children"), Output("table", "children")],
        [Input("design-value-id-ctrl", "value")]
    )
    def update_tablec2(design_value_id):
        name_and_units = (
            f"{design_value_id} ({config['dvs'][design_value_id]['units']})"
        )
        df = get_data(config, design_value_id, "table")
        df = (
            df[["Location", "Prov", "lon", "lat", "PCIC", "NBCC 2015"]]
                .round(3)
        )

        column_info = {
            "Location": {"name": ["", "Location"], "type": "text"},
            "Prov": {"name": ["", "Province"], "type": "text"},
            "lon": {"name": ["", "Longitude"], "type": "numeric"},
            "lat": {"name": ["", "Latitude"], "type": "numeric"},
            "PCIC": {"name": [name_and_units, "PCIC"], "type": "numeric"},
            "NBCC 2015": {
                "name": [name_and_units, "NBCC 2015"],
                "type": "numeric"
            },
        }

        return [
            name_and_units,
            dash_table.DataTable(
                columns=[{"id": id, **column_info[id]} for id in df.columns],
                style_table={
                    # "width": "100%",
                    # 'overflowX': 'auto',
                },
                style_cell={
                    "textAlign": "center",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "padding": "5px",
                    "width": "2em",
                    "minWidth": "2em",
                    "maxWidth": "2em",
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Location"},
                        "width": "5em",
                        "textAlign": "left",
                    },
                ],
                style_as_list_view=True,
                style_header={"backgroundColor": "white", "fontWeight": "bold"},
                page_action="none",
                filter_action="native",
                data=df.to_dict("records"),
            )
        ]

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
        Output("colourbar-range-ctrl-output-container", "children"),
        [Input("colourbar-range-ctrl", "value")],
    )
    def update_colourbar_range_label(value):
        return f"Range: {sigfigs(value[0])} to {sigfigs(value[1])}"

    @app.callback(
        [
            Output("colourbar-range-ctrl", "min"),
            Output("colourbar-range-ctrl", "max"),
            Output("colourbar-range-ctrl", "step"),
            Output("colourbar-range-ctrl", "marks"),
            Output("colourbar-range-ctrl", "value"),
        ],
        [
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ],
    )
    def update_slider(design_value_id, dataset_id):
        data = get_data(config, design_value_id, dataset_id)
        (dv_var_name,) = data.data_vars
        field = data[dv_var_name].values

        minimum = float(np.round(np.nanmin(field), 3))
        maximum = float(np.round(np.nanmax(field), 3))
        num_steps = 20
        step = (maximum - minimum) / (num_steps + 1)
        marks={
            x: str(sigfigs(x, 2))
            for x in (minimum * 1.008, (minimum + maximum) / 2, maximum)
        }
        default_value = [minimum, maximum]
        return [minimum, maximum, step, marks, default_value]

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
