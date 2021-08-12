import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np

from dve.config import dv_has_climate_regime
from dve.data import get_data
import dve.layout
from dve.math_utils import sigfigs


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        Output("colour-map-ctrl", "value"),
        [Input("design_variable", "value")],
    )
    def update_colour_map_ctrl_value(design_variable):
        return config["dvs"][design_variable]["colour_map"]

    @app.callback(
        Output("scale-ctrl", "value"), [Input("design_variable", "value")]
    )
    def update_scale_ctrl_value(design_variable):
        return config["dvs"][design_variable]["scale"]["default"]

    @app.callback(
        Output("scale-ctrl", "options"),
        [Input("design_variable", "value")],
    )
    def update_scale_ctrl_options(design_variable):
        options = [
            {
                **option,
                "disabled": (
                    option["value"] == "logarithmic"
                    and config["dvs"][design_variable]["scale"].get(
                        "disable_logarithmic", False
                    )
                ),
            }
            for option in dve.layout.scale_ctrl_options
        ]
        return options

    @app.callback(
        Output("colorscale_range_label", "children"),
        [Input("colourbar-range-ctrl", "value")],
    )
    def update_colourbar_range_label(value):
        return f"Range: {sigfigs(value[0])} to {sigfigs(value[1])}"

    @app.callback(
        [
            Output("colourbar-range-ctrl", "min"),
            Output("colourbar-range-ctrl", "max"),
            Output("colourbar-range-ctrl", "step"),
            Output("colourbar-range-ctrl", "marks"),
            Output("colourbar-range-ctrl", "value"),
        ],
        [
            Input("design_variable", "value"),
            Input("climate_regime", "value"),
            Input("historical_dataset_id", "value"),
            Input("future_dataset_id", "value"),
        ],
    )
    def update_slider(
        design_variable,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        if not dv_has_climate_regime(config, design_variable, climate_regime):
            raise PreventUpdate

        data = get_data(
            config,
            design_variable,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        field = data.dv_values()

        minimum = float(np.round(np.nanmin(field), 3))
        maximum = float(np.round(np.nanmax(field), 3))
        num_steps = 20
        step = (maximum - minimum) / (num_steps + 1)
        marks = {
            x: str(sigfigs(x, 2))
            for x in (minimum * 1.008, (minimum + maximum) / 2, maximum)
        }
        default_value = [minimum, maximum]
        return [minimum, maximum, step, marks, default_value]
