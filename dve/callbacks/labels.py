import logging
from dash.dependencies import Input, Output, State

from dve.config import (
    app_title, dv_dropdown_label, dv_dropdown_options,
    future_dataset_ctrl_options, climate_regime_ctrl_options,
    overlay_options_control_titles, overlay_options_section_title,
)

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

    @app.callback(
        Output("climate_regime", "options"),
        Input("language", "value"),
    )
    def update_climate_regime_options(lang):
        return climate_regime_ctrl_options(config, lang)

    @app.callback(
        Output("future_dataset_id", "options"),
        Input("language", "value"),
    )
    def update_future_dataset_id_options(lang):
        return future_dataset_ctrl_options(config, lang)

    @app.callback(
        Output("overlay_options_section_title", "children"),
        Input("language", "value"),
    )
    def update_overlay_options_section_title(lang):
        return overlay_options_section_title(config, lang)

    @app.callback(
        Output("overlay_options_control_titles", "children"),
        Input("language", "value"),
    )
    def update_overlay_options_control_titles(lang):
        return overlay_options_control_titles(config, lang)
