import logging

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from dve.callbacks.utils import triggered_by


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        Output("local_config", "data"),
        Output("design_variable", "value"),
        Output("apply_mask", "on"),
        Input("local_config", "modified_timestamp"),
        Input("design_variable", "value"),
        Input("apply_mask", "on"),
        State("local_config", "data"),
    )
    def update_local_config(
        local_config_ts, design_variable, apply_mask, local_config
    ):
        if local_config_ts is None or local_config is None:
            logger.debug(f"initializing local_config from config")
            return (
                {
                    "local_config_id": config["ui"]["local_config_id"],
                    "design_variable": config["ui"]["controls"][
                        "design-value-id"
                    ]["value"],
                    "mask": config["ui"]["controls"]["mask"]["on"],
                },
                dash.no_update,
                dash.no_update,
            )

        if (
            local_config.get("local_config_id")
            != config["ui"]["local_config_id"]
        ):
            logger.debug(f"updating local_config from config")
            return (
                {
                    "local_config_id": config["ui"]["local_config_id"],
                    "design_variable": local_config.get(
                        "design_variable",
                        config["ui"]["controls"]["design-value-id"]["value"],
                    ),
                    "mask": local_config.get(
                        "mask",
                        config["ui"]["controls"]["mask"]["on"],
                    ),
                },
                dash.no_update,
                dash.no_update,
            )

        ctx = dash.callback_context

        if triggered_by("local_config.", ctx):
            logger.debug("updating mask from local_config")
            design_variable_out = local_config["design_variable"]
            apply_mask_out = local_config["mask"]
        else:
            design_variable_out = dash.no_update
            apply_mask_out = dash.no_update

        if triggered_by("design_variable.", ctx):
            logger.debug("updating local_config from design_variable")
            local_config["design_variable"] = design_variable

        if triggered_by("apply_mask.", ctx):
            logger.debug("updating local_config from mask")
            local_config["mask"] = apply_mask

        return local_config, design_variable_out, apply_mask_out
