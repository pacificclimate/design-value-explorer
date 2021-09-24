import logging

import dash
from dash.dependencies import Input, Output, State

from dve.callbacks.utils import triggered_by
from dve.config import path_get

logger = logging.getLogger("dve")

# This variable defines the UI elements that mutually set and are set by the
# local configuration. To add a new UI element whose state is maintained in
# local storage, add a new item to this list.
ui_elements = (
    # (element id, element property, path in config)
    ("design_variable", "value", "ui.controls.design-value-id.value"),
    ("apply_mask", "on", "ui.controls.mask.on"),
)


def add(app, config):
    @app.callback(
        Output("local_config", "data"),
        *(Output(id, prop) for id, prop, _ in ui_elements),
        Input("local_config", "modified_timestamp"),
        *(Input(id, prop) for id, prop, _ in ui_elements),
        State("local_config", "data"),
    )
    def update_local_config(*args):
        # We have to unpack args like this because anything after a *args in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop this in there.
        local_config_ts, *ui_inputs, local_config = args

        config_vals = {
            element_id: path_get(config, path)
            for element_id, _, path in ui_elements
        }
        ui_elements_no_update = (dash.no_update,) * len(ui_elements)

        # If we have no local configuration, initialize it with values from
        # the static app config.
        if local_config_ts is None or local_config is None:
            logger.debug(f"initializing local_config from config")
            return (
                {
                    "local_config_id": config["ui"]["local_config_id"],
                    **config_vals,
                },
                *ui_elements_no_update,
            )

        # If the local configuration is out of date, update it from the static
        # app config, preserving existing values of local config where possible.
        if (
            local_config.get("local_config_id")
            != config["ui"]["local_config_id"]
        ):
            logger.debug(f"updating local_config from config")
            return (
                {
                    "local_config_id": config["ui"]["local_config_id"],
                    **{
                        element_id: local_config.get(
                            element_id, config_vals[element_id]
                        )
                        for element_id, _, path in ui_elements
                    },
                },
                *ui_elements_no_update,
            )

        # Strictly speaking, the callback could be triggered by any combination
        # of its inputs, but in practice it is exactly one. Here we assume
        # that the trigger is either an update of local config or one or more
        # UI element changes, never both.
        ctx = dash.callback_context
        if triggered_by("local_config.", ctx):
            # A local config change triggered this callback. Therefore update
            # the UI elements with values from local config, and don't update
            # local config.
            local_config_output = dash.no_update
            ui_outputs = [
                local_config[element_id] for element_id, _, path in ui_elements
            ]
        else:
            # A UI element triggered this callback. Therefore update the local
            # config and don't update the UI elements.
            local_config_output = local_config
            for element_id, input_value in zip(
                (e[0] for e in ui_elements), ui_inputs
            ):
                if triggered_by(f"{element_id}.", ctx):
                    local_config_output[element_id] = input_value
            ui_outputs = ui_elements_no_update

        return (local_config_output, *ui_outputs)
