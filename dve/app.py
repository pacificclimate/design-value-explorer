import yaml

import dve
import dve.callbacks.map_figure
import dve.callbacks.table_c2
import dve.callbacks.colour_scale
import dve.callbacks.map_pointer
import dve.data
import dve.layout

import dash
import dash_bootstrap_components as dbc
from .download_utils import download_base_url

import flask
import os
import warnings
import logging


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

    # Add layout
    app.layout = dve.layout.main(config)

    # Add callbacks
    dve.callbacks.table_c2.add_callbacks(app, config)
    dve.callbacks.colour_scale.add_callbacks(app, config)
    dve.callbacks.map_pointer.add_callbacks(app, config)
    dve.callbacks.map_figure.add_callbacks(app, config)

    # Add routes
    @app.server.route(f"{str(download_base_url())}/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join("/downloads/by-location"), filename
        )

    return app
