import logging
from dash.dependencies import Input, Output, State

from dve.config import app_title, dv_dropdown_label, dv_dropdown_options

logger = logging.getLogger(__name__)


def add(app, config):
    @app.callback(
        Output("app_title", "children"),
        Input("language", "value"),
    )
    def update_app_title(lang):
        return app_title(config, lang)

    @app.callback(
        Output("dv_dropdown_label", "children"),
        Input("language", "value"),
    )
    def update_dv_dropdown_label(lang):
        return dv_dropdown_label(config, lang)

    @app.callback(
        Output("design_variable", "options"),
        Input("language", "value"),
    )
    def update_design_variable_options(lang):
        return dv_dropdown_options(config, lang)
