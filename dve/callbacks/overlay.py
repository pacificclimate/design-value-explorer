import logging
from dash.dependencies import Input, Output


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        Output("future_dataset_id", "disabled"),
        [Input("climate_regime", "value")],
    )
    def update_dataset_ctrl_disable(climate_regime):
        return climate_regime != "future"

    @app.callback(
        Output("show_stations", "disabled"), Input("climate_regime", "value")
    )
    def update_stations_ctrl_disable(climate_regime):
        return climate_regime == "future"
