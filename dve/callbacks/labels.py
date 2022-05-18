import logging
from dash.dependencies import Input, Output, State

from dve.config import app_title

logger = logging.getLogger(__name__)


def add(app, config):
    @app.callback(
        Output("app_title", "children"),
        Input("language", "value"),
    )
    def update_app_title(lang):
        return app_title(config, lang)
