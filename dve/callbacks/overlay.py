from dash.dependencies import Input, Output


def add(app, config):
    @app.callback(
        Output("dataset-ctrl", "disabled"),
        [Input("climate-ctrl", "value")],
    )
    def thingy(climate_regime):
        return climate_regime != "historical"
