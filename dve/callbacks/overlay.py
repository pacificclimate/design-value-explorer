import logging

import dash
from dash.dependencies import Input, Output

from dve.config import dv_has_climate_regime
from dve.layout import climate_regime_ctrl_options


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        [
            Output("climate-regime-ctrl", "options"),
            Output("climate-regime-ctrl", "value"),
        ],
        [Input("design-value-id-ctrl", "value")],
    )
    def update_dataset_ctrl_value(design_value_id):
        """
        If this DV does not have historical data, set climate regime
        to future and disable historical option. Otherwise leave things alone.
        """
        if dv_has_climate_regime(config, design_value_id, "historical"):
            return climate_regime_ctrl_options, dash.no_update
        options = [
            {**option, "disabled": option["value"] == "historical"}
            for option in climate_regime_ctrl_options
        ]
        return options, "future"

    @app.callback(
        [
            Output("historical-dataset-ctrl", "disabled"),
            Output("future-dataset-ctrl", "disabled"),
        ],
        [Input("climate-regime-ctrl", "value")],
    )
    def update_dataset_ctrl_disable(climate_regime):
        logger.debug("update_dataset_ctrl_disable")
        return [climate_regime != x for x in ("historical", "future")]
