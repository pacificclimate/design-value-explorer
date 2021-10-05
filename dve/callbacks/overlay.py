import logging

import dash
from dash.dependencies import Input, Output

from dve.config import dv_has_climate_regime
from dve.layout import climate_regime_ctrl_options


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        [
            Output("climate_regime", "options"),
            Output("climate_regime", "value"),
        ],
        [Input("design_variable", "value")],
    )
    def update_dataset_ctrl_value(design_variable):
        """
        If this DV does not have historical data, set climate regime
        to future and disable historical option. Otherwise leave things alone.
        """
        if dv_has_climate_regime(config, design_variable, "historical"):
            return climate_regime_ctrl_options(config), dash.no_update
        options = [
            {**option, "disabled": option["value"] == "historical"}
            for option in climate_regime_ctrl_options(config)
        ]
        return options, "future"

    @app.callback(
        Output("future_dataset_id", "disabled"),
        [Input("climate_regime", "value")],
    )
    def update_dataset_ctrl_disable(climate_regime):
        return climate_regime != "future"

    @app.callback(
        Output("show_stations", "disabled"),
        Input("climate_regime", "value"),
    )
    def update_stations_ctrl_disable(climate_regime):
        return climate_regime == "future"
