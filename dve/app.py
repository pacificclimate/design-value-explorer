import json
import yaml

import dve
import dve.app_.map_figure
import dve.app_.table_c2
import dve.app_.colour_scale
import dve.app_.map_pointer
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

    dve.app_.map_pointer.add_callbacks(app, config)

    dve.app_.map_figure.add_callbacks(app, config)

    @app.server.route(f"{str(download_base_url())}/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join("/downloads/by-location"), filename
        )

    return app
