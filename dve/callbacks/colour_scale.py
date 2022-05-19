import logging

from dash.dependencies import Input, Output, State

import numpy as np

from dve.config import (
    dv_roundto, dv_colour_scale_disable_logarithmic, filepath_for,
    colorscale_options_label_range,
)
from dve.data import get_data_object
import dve.layout
from dve.math_utils import sigfigs, round_to_multiple

logger = logging.getLogger(__name__)
lang = "en"  # TODO: Replace with language selection


def add(app, config):
    @app.callback(
        Output("color_scale_type", "options"),
        Input("design_variable", "value"),
        Input("climate_regime", "value"),
        Input("language", "value"),
    )
    def update_scale_ctrl_options(design_variable, climate_regime, lang):
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
            for option in dve.layout.scale_ctrl_options(config, lang)
        ]
        return options

    @app.callback(
        Output("colorscale_options_label_range", "children"),
        Input("color_scale_data_range", "value"),
        Input("language", "value"),
    )
    def update_colorscale_options_label_range(range, lang):
        return colorscale_options_label_range(
            config, lang, min=sigfigs(range[0]), max=sigfigs(range[1])
        )

    @app.callback(
        Output("color_scale_data_range", "min"),
        Output("color_scale_data_range", "max"),
        Output("color_scale_data_range", "step"),
        Output("color_scale_data_range", "marks"),
        Output("color_scale_data_range", "value"),
        Input("design_variable", "value"),
        Input("climate_regime", "value"),
        # Input("historical_dataset_id", "value"),
        Input("future_dataset_id", "value"),
    )
    def update_slider(
        design_variable,
        climate_regime,
        # historical_dataset_id,
        future_dataset_id,
    ):
        historical_dataset_id = "reconstruction"

        # Return a dummy setup there is no raster data file defined for this DV.
        if (
            filepath_for(
                config,
                design_variable,
                climate_regime,
                historical_dataset_id=historical_dataset_id,
                future_dataset_id=future_dataset_id,
            )
            is None
        ):
            return (0, 0, 1, {}, (0, 0))

        data = get_data_object(
            config,
            design_variable,
            climate_regime,
            historical_dataset_id=historical_dataset_id,
            future_dataset_id=future_dataset_id,
        )
        field = data.dv_values()

        roundto = dv_roundto(config, design_variable, climate_regime)
        minimum = round_to_multiple(np.nanmin(field), roundto, "down")
        maximum = round_to_multiple(np.nanmax(field), roundto, "up")
        num_steps = 20
        step = (maximum - minimum) / num_steps
        marks = {
            str(x): str(x)
            for x in (
                round_to_multiple(minimum + k * step, roundto)
                for k in range(0, num_steps + 1, 4)
            )
        }
        default_value = (minimum, maximum)
        return (minimum, maximum, step, marks, default_value)
