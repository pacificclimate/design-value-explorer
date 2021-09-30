"""
This module implements the mutual update relationship between local
configuration and the UI elements related to that configuration.

"Local configuration" means per-client configuration/preferences stored in
browser local storage. (Note: A "client" is a single instance of a web browser;
DVE does not provide for users with identities separate from browser instances,
nor the accompanying notions of signin etc.)

Local configuration includes:

- Simple options (Mask, Stations, Grid, Num Colours), which are independent
  of DV and Period
- Per-DV/Period options (Colour Map, Scale)

When a client (web browser instance) first loads DVE, default settings for these
options are loaded from a global, client-independent configuration. Thereafter,
DVE uses the local configuration to manage these values: The app
sets the local configuration according to the user's selections of
these options in the UI. Conversely, when the app is reloaded by the same
client, the locally stored configuration is used to set the default
settings of the UI elements. In addition, per-DV/Period UI elements are set
to the locally stored value when either DV or Period is changed. This means
that the app remembers a user's preference for how to view each dataset.

Implementation notes:
- Local configuration is stored using a `dcc.Store` layout element with
  id `"local_config"`.
- The mutual relationship between local config and the UI settings requires
  circular updates. That is permitted by Dash only in a single callback;
  circularity due to two or more callbacks is forbidden.
  For more information, see https://dash.plotly.com/advanced-callbacks
- There are some complications due to using `dcc.Store`: Specifically
  see "Retrieving the initial store data" in
  https://dash.plotly.com/dash-core-components/store . We follow that advice.
- To accommodate changes in the contents of local config (e.g., what options
  are managed by it, its layout), the global config value `local_config.version`
  is stored locally and compared on each load. If it differs, the local config
  is reloaded from global config, preserving local config settings if possible.
"""

import logging

import dash
from dash.dependencies import Input, Output, State

from dve.callbacks.utils import triggered_by
from dve.dict_utils import path_get, path_set

logger = logging.getLogger("dve")


# Helper
def expanded_path(path, **kwargs):
    """Expands a path by substituting interpolated values."""
    return path.format(**kwargs)


def add(app, config):
    # These variables define the UI elements that mutually set and are set by
    # local configuration. To add a new UI element whose state is maintained in
    # local storage, add a new item to a list.
    updatable_ui_elements = [
        {"id": "apply_mask", "prop": "on", "get": "ui.controls.mask.on"},
        {
            "id": "show_stations",
            "prop": "on",
            "get": "ui.controls.stations.on",
        },
        {"id": "show_grid", "prop": "on", "get": "ui.controls.grid.on"},
        {
            "id": "num_colors",
            "prop": "value",
            "get": "ui.controls.num-colours.value",
        },
        {
            "id": "color_map",
            "prop": "value",
            "get": "dvs.{design_variable}.{climate_regime}.colour_map",
        },
        {
            "id": "color_scale_type",
            "prop": "value",
            "get": "dvs.{design_variable}.{climate_regime}.scale.default",
        },
    ]

    # Helpers
    ui_elements_no_update = (dash.no_update,) * len(updatable_ui_elements)

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
        # We have to unpack args like this because anything after a `*args` in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop that in there.
        (
            local_config_ts,
            design_variable,
            climate_regime,
            *updatable_ui_inputs,
            local_config,
        ) = args

        # Helper
        def init_local_config(preserve_local=True):
            result = {}
            v_path = "local_config.version"
            path_set(result, v_path, path_get(config, v_path))

            def update_result(get_path, put_path):
                global_value = path_get(config, get_path)
                path_set(
                    result,
                    put_path,
                    path_get(local_config, get_path, default=global_value)
                    if preserve_local
                    else global_value,
                )

            for e in updatable_ui_elements:
                get_path = e["get"]
                put_path = e.get("put", get_path)
                dvs = (
                    config["ui"]["dvs"]
                    if "{design_variable}" in put_path
                    else (None,)
                )
                crs = (
                    ("historical", "future")
                    if "{climate_regime}" in put_path
                    else (None,)
                )
                for dv in dvs:
                    for cr in crs:
                        update_result(
                            expanded_path(
                                get_path, design_variable=dv, climate_regime=cr
                            ),
                            expanded_path(
                                put_path, design_variable=dv, climate_regime=cr
                            ),
                        )

            return result

        # If we have no local configuration, initialize it with values from
        # the global app config.
        if local_config_ts is None or local_config is None:
            logger.debug(f"initializing local_config from config")
            return (
                init_local_config(preserve_local=False),
                *ui_elements_no_update,
            )

        # If the local configuration is out of date, update it from the global
        # app config, preserving existing values of local config where possible.
        if path_get(local_config, "local_config.version") != path_get(
            config, "local_config.version"
        ):
            logger.debug(f"updating local_config from config")
            return (
                init_local_config(preserve_local=True),
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
            # TODO: This happens when the client app is reloaded and whenever
            #  local_config is updated. It would be better if we could
            #  distinguish app reloads from updates so that we don't do
            #  unnecessary updates to the ui elements. (The latter also seems
            #  it should create an infinite loop of updates, but Dash apparently
            #  prevents that.) I suspect there is a different and better way to
            #  structure this callback. This does work.
            # TODO: Place in separate callbacks
            logger.debug("updating UI elements from local config")
            return (
                dash.no_update,
                *(
                    path_get(
                        local_config,
                        expanded_path(
                            e["get"],
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
        # TODO: Place in separate callback
        if triggered_by(("design_variable.", "climate_regime."), ctx):
            logger.debug("updating colour scale options")
            return (
                dash.no_update,
                *(
                    path_get(
                        local_config,
                        expanded_path(
                            e["get"],
                            design_variable=design_variable,
                            climate_regime=climate_regime,
                        ),
                    )
                    for e in updatable_ui_elements
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
                get_path = element["get"]
                put_path = element.get("put", get_path)
                path_set(
                    local_config_output,
                    expanded_path(
                        put_path,
                        design_variable=design_variable,
                        climate_regime=climate_regime,
                    ),
                    input_value,
                )
        return (local_config_output, *ui_elements_no_update)
