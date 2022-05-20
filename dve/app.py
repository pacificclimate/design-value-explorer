import os
import warnings
import logging
import logging.config
import yaml
from yamlinclude import YamlIncludeConstructor

import dve
import dve.config
import dve.callbacks.local_preferences
import dve.callbacks.help
import dve.callbacks.map_figure
import dve.callbacks.table_c2
import dve.callbacks.colour_scale
import dve.callbacks.map_pointer
import dve.callbacks.overlay
import dve.callbacks.labels
import dve.data
import dve.layout

import dash
import dash_bootstrap_components as dbc
from .download_utils import download_base_url

import flask


default_log_config_filepath = "app-logging.yml"
default_app_config_filepath = "app-config.yml"

# Add !include tag processor to PyYAML loader
# TODO: Can/should this go inside `make_app`?
YamlIncludeConstructor.add_to_loader_class(
    loader_class=yaml.FullLoader, base_dir="."
)


def make_dash_app(config):
    warnings.filterwarnings("ignore")

    # Initialize Dash app
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = "Pacific Climate Impacts Consortium Design Value Explorer"
    app.config.suppress_callback_exceptions = True

    # Add layout
    app.layout = dve.layout.main(app, config)

    # Add callbacks
    dve.callbacks.local_preferences.add(app, config)
    dve.callbacks.help.add(app, config)
    dve.callbacks.table_c2.add(app, config)
    dve.callbacks.overlay.add(app, config)
    dve.callbacks.colour_scale.add(app, config)
    dve.callbacks.map_pointer.add(app, config)
    dve.callbacks.map_figure.add(app, config)
    dve.callbacks.labels.add(app, config)

    # Add routes
    @app.server.route(f"{str(download_base_url())}/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join("/downloads/by-location"), filename
        )

    return app


def make_app(
    log_config_filepath=default_log_config_filepath,
    app_config_filepath=default_app_config_filepath,
):
    """
    Main app factory. Configures app logging, reads app config file, causes
    Dash app to be created, returns Dash app.

    This factory is called by both the command line development interface and
    the production WSGI interface.

    App logging is separate from HTTP server logging, since the server is
    external to and independent of the app. The HTTP server is responsible
    for configuration its own logging.

    App logging configuration is also separate from main app configuration.
    Logging configuration must be done before any logging is done, and main
    app configuration logs important messages. With sufficient cleverness the
    two could be managed in one file, but it's not worth it.

    :param log_config_filepath: Filepath of app logging configuration file.
    :param app_config_filepath: Filepath of app configuration file.
    :return: a Dash app
    """

    # Configure app logging.
    with open(log_config_filepath, "r") as log_config_file:
        logging_config = yaml.safe_load(log_config_file)
    logging.config.dictConfig(logging_config)

    logger = logging.getLogger("dve")

    logger.debug("Loading app configuration")
    with open(app_config_filepath, "r") as config_file:
        config = yaml.load(config_file)
    logger.debug(f"Configuration loaded.")

    dve.config.validate(config)

    app = make_dash_app(config)

    return app


def make_wsgi_app():
    """
    This is the entry point for Gunicorn or other external HTTP servers.
    It returns a WSGI app. As recommended by Gunicorn, it does not receive
    arguments but instead loads values from environment variables, namely:

    - Logging config filepath: `DVE_LOG_CONFIG`.
    - App config filepath: `DVE_APP_CONFIG`.
    """
    log_config_filepath = os.getenv(
        "DVE_LOG_CONFIG", default_log_config_filepath
    )
    app_config_filepath = os.getenv(
        "DVE_APP_CONFIG", default_app_config_filepath
    )
    app = make_app(
        log_config_filepath=log_config_filepath,
        app_config_filepath=app_config_filepath,
    )
    return app.server
