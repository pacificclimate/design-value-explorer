import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np

from dve.config import dv_has_climate_regime
from dve.data2 import get_data
import dve.layout
from dve.math_utils import sigfigs


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        Output("colour-map-ctrl", "value"),
        [Input("design-value-id-ctrl", "value")],
    )
    def update_colour_map_ctrl_value(design_value_id):
        return config["dvs"][design_value_id]["colour_map"]

    @app.callback(
        Output("scale-ctrl", "value"), [Input("design-value-id-ctrl", "value")]
    )
    def update_scale_ctrl_value(design_value_id):
        return config["dvs"][design_value_id]["scale"]["default"]

    @app.callback(
        Output("scale-ctrl", "options"),
        [Input("design-value-id-ctrl", "value")],
    )
    def update_scale_ctrl_options(design_value_id):
        options = [
            {
                **option,
                "disabled": (
                    option["value"] == "logarithmic"
                    and config["dvs"][design_value_id]["scale"].get(
                        "disable_logarithmic", False
                    )
                ),
            }
            for option in dve.layout.scale_ctrl_options
        ]
        return options

    @app.callback(
        Output("colourbar-range-ctrl-output-container", "children"),
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
            Input("design-value-id-ctrl", "value"),
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
        ],
    )
    def update_slider(design_value_id, climate_regime, historical_dataset_id, future_dataset_id):
        if not dv_has_climate_regime(
            config, design_value_id, climate_regime
        ):
            raise PreventUpdate

        logger.debug("update_slider: get_data")
        data = get_data(config, design_value_id, climate_regime, historical_dataset_id, future_dataset_id)
        field = data.dv.values

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
