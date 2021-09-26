import logging

import dash
from dash.dependencies import Input, Output, State

from dve.callbacks.utils import triggered_by
from dve.dict_utils import path_get, path_set

logger = logging.getLogger("dve")

# This variable defines the UI elements that mutually set and are set by the
# local configuration. To add a new UI element whose state is maintained in
# local storage, add a new item to this list.
simple_options_ui_elements = (
    # TODO: Probably have to do this as a special case ... later
    # {
    #     "id": "design_variable",
    #     "prop": "value",
    #     "path": "ui.controls.design-value-id.value",
    # },
    {"id": "apply_mask", "prop": "on", "path": "ui.controls.mask.on"},
    {"id": "show_stations", "prop": "on", "path": "ui.controls.stations.on"},
    {"id": "show_grid", "prop": "on", "path": "ui.controls.grid.on"},
)

colour_scale_options_ui_elements = (
    {
        "id": "color_map",
        "prop": "value",
        "path": "dvs.{design_variable}.{climate_regime}.colour_map",
    },
    {
        "id": "color_scale_type",
        "prop": "value",
        "path": "dvs.{design_variable}.{climate_regime}.scale.default",
    },
)

updatable_ui_elements = (
    simple_options_ui_elements + colour_scale_options_ui_elements
)


# Helper
def expanded_path(ui_element, **kwargs):
    """Expands the path in `ui_element` by substituting interpolated
    values."""
    return ui_element["path"].format(**kwargs)


def add(app, config):
    @app.callback(
        Output("local_config", "data"),
        *(Output(e["id"], e["prop"]) for e in updatable_ui_elements),
        Input("local_config", "modified_timestamp"),
        Input("design_variable", "value"),
        Input("climate_regime", "value"),
        *(Input(e["id"], e["prop"]) for e in updatable_ui_elements),
        State("local_config", "data"),
    )
    def update_local_config(*args):
        """
        This callback implements the mutual update relationship between local
        configuration (i.e., per-client configuration stored in browser local
        storage) and the UI elements related to that configuration. For example:
        The "Mask" UI element defaults to "on". That default is stored in the
        global, client-independent configuration. Each client (web browser
        instance) has a local configuration storage in which the user's setting
        of this UI selection is stored. That local setting is applied to Mask
        when the app is started again in web browser after being closed.

        There are two classes of UI settings that are stored in local
        configuration:
        - A subset of the Overlay Options (Mask, Stations, Grid)
        - A subset of the Colour Scale Options (all?)

        The Overlay Options settings are independent of (i.e., apply to all)
        Design Variable and Period / Global Warming choices.

        The Colour Scale Options are managed per Design Variable and Period
        choice. For example, the choice of Colour Map is specific to the DV
        and Period chosen; selecting a different DV or Period means a different
        Colour Map (although the user is free to choose the same Colour Map for
        different DVs and Periods).

        Defaults for local configuration are loaded from global configuration.


        """

        # We have to unpack args like this because anything after a *args in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop this in there.
        (
            local_config_ts,
            design_variable,
            climate_regime,
            *updatable_ui_inputs,
            local_config,
        ) = args

        # Helper
        simple_options_ui_elements_no_update = (dash.no_update,) * len(
            simple_options_ui_elements
        )
        colour_scale_options_ui_elements_no_update = (dash.no_update,) * len(
            colour_scale_options_ui_elements
        )

        # Helper
        def init_local_config(preserve_local=True):
            result = {"local_config_id": config["ui"]["local_config_id"]}

            def update_result(path):
                global_value = path_get(config, path)
                path_set(
                    result,
                    path,
                    path_get(local_config, path, default=global_value)
                    if preserve_local
                    else global_value,
                )

            for e in simple_options_ui_elements:
                update_result(
                    expanded_path(
                        e,
                        design_variable=design_variable,
                        climate_regime=climate_regime,
                    )
                )

            for e in colour_scale_options_ui_elements:
                for dv in config["ui"]["dvs"]:
                    for cr in ("historical", "future"):
                        update_result(
                            expanded_path(
                                e, design_variable=dv, climate_regime=cr
                            )
                        )

            return result

        # If we have no local configuration, initialize it with values from
        # the global app config.
        if local_config_ts is None or local_config is None:
            logger.debug(f"initializing local_config from config")
            return (
                init_local_config(preserve_local=False),
                *simple_options_ui_elements_no_update,
                *colour_scale_options_ui_elements_no_update,
            )

        # If the local configuration is out of date, update it from the global
        # app config, preserving existing values of local config where possible.
        if (
            local_config.get("local_config_id")
            != config["ui"]["local_config_id"]
        ):
            logger.debug(f"updating local_config from config")
            return (
                init_local_config(preserve_local=True),
                *simple_options_ui_elements_no_update,
                *colour_scale_options_ui_elements_no_update,
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
            # TODO: This seems to happen too often
            logger.debug("updating UI elements from local config")
            return (
                dash.no_update,
                *(
                    path_get(
                        local_config,
                        expanded_path(
                            e,
                            design_variable=design_variable,
                            climate_regime=climate_regime,
                        ),
                    )
                    for e in updatable_ui_elements
                ),
            )

        # The Design Variable or Period (climate_regime) element triggered this
        # callback. Therefore update the Colour Scale options UI elements from
        # local configuration and don't update the local config or the Overlay
        # Options UI elements.
        if triggered_by(("design_variable.", "climate_regime."), ctx):
            logger.debug("updating colour scale options")
            return (
                dash.no_update,
                *simple_options_ui_elements_no_update,
                *(
                    path_get(
                        local_config,
                        expanded_path(
                            e,
                            design_variable=design_variable,
                            climate_regime=climate_regime,
                        ),
                    )
                    for e in colour_scale_options_ui_elements
                ),
            )

        # An Overlay Options or Colour Scale Options UI element triggered this
        # callback. Therefore update the local config and don't update the UI
        # elements.
        logger.debug("updating local config from UI change")
        local_config_output = local_config
        for element, input_value in zip(
            updatable_ui_elements, updatable_ui_inputs
        ):
            if triggered_by(f'{element["id"]}.', ctx):
                path_set(
                    local_config_output,
                    expanded_path(
                        element,
                        design_variable=design_variable,
                        climate_regime=climate_regime,
                    ),
                    input_value,
                )
        return (
            local_config_output,
            *simple_options_ui_elements_no_update,
            *colour_scale_options_ui_elements_no_update,
        )
