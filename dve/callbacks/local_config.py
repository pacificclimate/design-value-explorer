import logging

import dash
from dash.dependencies import Input, Output, State

from dve.callbacks.utils import triggered_by
from dve.dict_utils import path_get, path_set

logger = logging.getLogger("dve")

# This variable defines the UI elements that mutually set and are set by the
# local configuration. To add a new UI element whose state is maintained in
# local storage, add a new item to this list.
ui_elements = (
    # TODO: Probably have to do this as a special case ... later
    # {
    #     "id": "design_variable",
    #     "prop": "value",
    #     "path": "ui.controls.design-value-id.value",
    # },
    {"id": "apply_mask", "prop": "on", "path": "ui.controls.mask.on"},
    {
        "id": "show_stations",
        "prop": "on",
        "path": "ui.controls.stations.on",
    },
    {"id": "show_grid", "prop": "on", "path": "ui.controls.grid.on"},
    # {
    #     "id": "color_map",
    #     "prop": "value",
    #     "path": "dvs.{design_value}.{climate_regime}.{id}",
    # },
)


def add(app, config):
    @app.callback(
        Output("local_config", "data"),
        *(Output(e["id"], e["prop"]) for e in ui_elements),
        Input("design_variable", "value"),
        Input("climate_regime", "value"),
        Input("local_config", "modified_timestamp"),
        *(Input(e["id"], e["prop"]) for e in ui_elements),
        State("local_config", "data"),
    )
    def update_local_config(*args):
        # We have to unpack args like this because anything after a *args in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop this in there.
        local_config_ts, design_variable, climate_regime, *ui_inputs, local_config = args

        # Helper
        ui_elements_no_update = (dash.no_update,) * len(ui_elements)

        # Helper
        def expanded_path(ui_element):
            """Expands the path in `ui_element` by substituting certain
            variables."""
            return ui_element["path"].format(
                design_variable=design_variable,
                climate_regime=climate_regime,
            )

        # If we have no local configuration, initialize it with values from
        # the static app config.
        if local_config_ts is None or local_config is None:
            logger.debug(f"initializing local_config from config")
            local_config_output = {
                "local_config_id": config["ui"]["local_config_id"]
            }
            for e in ui_elements:
                path = expanded_path(e)
                path_set(local_config_output, path, path_get(config, path))
            return (local_config_output, *ui_elements_no_update)

        # If the local configuration is out of date, update it from the static
        # app config, preserving existing values of local config where possible.
        if (
            local_config.get("local_config_id")
            != config["ui"]["local_config_id"]
        ):
            logger.debug(f"updating local_config from config")
            local_config_output = {
                "local_config_id": config["ui"]["local_config_id"]
            }
            for e in ui_elements:
                path = expanded_path(e)
                path_set(
                    local_config_output,
                    path,
                    path_get(local_config, path, path_get(config, path))
                )
            return (local_config_output, *ui_elements_no_update)

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
                path_get(local_config, expanded_path(e))
                for e in ui_elements
            ]
        else:
            # A UI element triggered this callback. Therefore update the local
            # config and don't update the UI elements.
            local_config_output = local_config
            for element, input_value in zip(ui_elements, ui_inputs):
                if triggered_by(f'{element["id"]}.', ctx):
                    path_set(
                        local_config_output,
                        expanded_path(element),
                        input_value
                    )
            ui_outputs = ui_elements_no_update

        return (local_config_output, *ui_outputs)
