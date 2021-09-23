import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np

from dve.config import (
    dv_has_climate_regime,
    dv_roundto,
    dv_colour_map,
    dv_colour_scale_default,
    dv_colour_scale_disable_logarithmic,
)
from dve.data import get_data
import dve.layout
from dve.math_utils import sigfigs, round_to_multiple

logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        Output("color_map", "value"),
        [Input("design_variable", "value"), Input("climate_regime", "value")],
    )
    def update_colour_map_ctrl_value(design_variable, climate_regime):
        return dv_colour_map(config, design_variable, climate_regime)

    @app.callback(
        Output("color_scale_type", "value"),
        [Input("design_variable", "value"), Input("climate_regime", "value")],
    )
    def update_colour_scale_type(design_variable, climate_regime):
        return dv_colour_scale_default(config, design_variable, climate_regime)

    @app.callback(
        Output("color_scale_type", "options"),
        [Input("design_variable", "value"), Input("climate_regime", "value")],
    )
    def update_scale_ctrl_options(design_variable, climate_regime):
        options = [
            {
                **option,
                "disabled": (
                    option["value"] == "logarithmic"
                    and dv_colour_scale_disable_logarithmic(
                        config, design_variable, climate_regime
                    )
                ),
            }
            for option in dve.layout.scale_ctrl_options
        ]
        return options

    @app.callback(
        Output("colorscale_options_label_range", "children"),
        [Input("color_scale_data_range", "value")],
    )
    def update_colourbar_range_label(range):
        return f"Range: {sigfigs(range[0])} to {sigfigs(range[1])}"

    @app.callback(
        [
            Output("color_scale_data_range", "min"),
            Output("color_scale_data_range", "max"),
            Output("color_scale_data_range", "step"),
            Output("color_scale_data_range", "marks"),
            Output("color_scale_data_range", "value"),
        ],
        [
            Input("design_variable", "value"),
            Input("climate_regime", "value"),
            # Input("historical_dataset_id", "value"),
            Input("future_dataset_id", "value"),
        ],
    )
    def update_slider(
        design_variable,
        climate_regime,
        # historical_dataset_id,
        future_dataset_id,
    ):
        if not dv_has_climate_regime(config, design_variable, climate_regime):
            raise PreventUpdate

        data = get_data(
            config,
            design_variable,
            climate_regime,
            historical_dataset_id="reconstruction",
            future_dataset_id=future_dataset_id,
        )
        field = data.dv_values()

        roundto = dv_roundto(config, design_variable, climate_regime)
        minimum = round_to_multiple(np.nanmin(field), roundto, "down")
        maximum = round_to_multiple(np.nanmax(field), roundto, "up")
        num_steps = 20
        step = (maximum - minimum) / (num_steps + 1)
        marks = {x: str(x) for x in (minimum, (minimum + maximum) / 2, maximum)}
        default_value = (minimum, maximum)
        return (minimum, maximum, step, marks, default_value)
