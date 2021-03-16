from dash.dependencies import Input, Output


def add(app, config):
    @app.callback(
        [
            Output("historical-dataset-ctrl", "disabled"),
            Output("future-dataset-ctrl", "disabled"),
        ],
        [Input("climate-regime-ctrl", "value")],
    )
    def update_dataset_ctrl_disable(climate_regime):
        return [climate_regime != x for x in ("historical", "future")]
