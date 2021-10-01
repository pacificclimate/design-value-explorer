"""
This module implements the mutual update relationship between local
configuration and the UI elements related to that configuration.

"Local configuration" means per-client configuration/preferences stored in
browser local storage. (Note: A "client" is a single instance of a web browser;
DVE does not provide for users with identities separate from browser instances,
nor the accompanying notions of signin etc.)

Local configuration includes:

- Simple options (e.g., Mask, Stations, Grid), which are independent
  of DV and Period
- Per-DV/Period options (Colour Map, Scale, Num Colours)

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

- The mutual-update relationship between local config and the UI settings
  requires what Dash calls circular updates. This is permitted only when the
  circularity is contained in a single callback; circularity due to two or more
  callbacks is forbidden in Dash. For more information, see
  https://dash.plotly.com/advanced-callbacks
  HOWEVER, it appears that our particular case evades that rule. I *think*
  the reason is that the local storage timestamp
  `Input("local_config", "modified_timestamp")`
  is a proxy for updates to the *data* in the local storage. Why this doesn't
  cause an infinite update loop is not clear to me, but it doesn't, and it
  simplifies the code.
  IF in future we get circularity problems, then the callbacks will have to be
  combined into one. The code gets uglier, but it's not terribly hard.

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


# Helpers

def global_path(element, **kwargs):
    """
    Return the path for the value of a UI element in the global config.
    Return it raw (unsubstituted) if no kwargs are supplied, otherwise,
    substitute (string.format) the supplied kwargs in the raw path.
    """
    raw = element["global"]
    if len(kwargs) == 0:
        return raw
    return raw.format(**kwargs)


def local_path(element, **kwargs):
    """
    Return the path for the value of a UI element in the local config.
    Return it raw (unsubstituted) if no kwargs are supplied, otherwise,
    substitute (string.format) the supplied kwargs in the raw path.
    """
    raw = element.get("local", element["global"])
    if len(kwargs) == 0:
        return raw
    return raw.format(**kwargs)


def add(app, config):
    # These variables define the UI elements that mutually set and are set by
    # local configuration. To add a new UI element whose state is maintained in
    # local storage, add a new item to a list.
    updatable_ui_elements = [
        {"id": "apply_mask", "prop": "on", "global": "ui.controls.mask.on"},
        {"id": "show_stations", "prop": "on", "global": "ui.controls.stations.on"},
        {"id": "show_grid", "prop": "on", "global": "ui.controls.grid.on"},
        {
            "id": "num_colors",
            "prop": "value",
            "global": "ui.controls.num-colours.value",
            "local": "dvs.{design_variable}.{climate_regime}.num_colours",
        },
        {
            "id": "color_map",
            "prop": "value",
            "global": "dvs.{design_variable}.{climate_regime}.colour_map",
        },
        {
            "id": "color_scale_type",
            "prop": "value",
            "global": "dvs.{design_variable}.{climate_regime}.scale.default",
        },
    ]

    @app.callback(
        Output("local_config", "data"),
        Input("local_config", "modified_timestamp"),
        *(Input(e["id"], e["prop"]) for e in updatable_ui_elements),
        State("local_config", "data"),
        State("design_variable", "value"),
        State("climate_regime", "value"),
    )
    def update_local_config(*args):
        # We have to unpack args like this because anything after a `*args` in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop that in there.
        (
            local_config_ts,
            *updatable_ui_inputs,
            local_config,
            design_variable,
            climate_regime,
        ) = args
        logger.debug(f"update_local_config local_config_ts={local_config_ts}")

        # Helper
        def init_local_config(preserve_local=True):
            result = {}
            v_path = "local_config.version"
            path_set(result, v_path, path_get(config, v_path))

            def update_result(gpath, lpath):
                global_value = path_get(config, gpath)
                path_set(
                    result,
                    lpath,
                    path_get(local_config, gpath, default=global_value)
                    if preserve_local
                    else global_value,
                )

            for e in updatable_ui_elements:
                raw_put_path = local_path(e)
                dvs = (
                    config["ui"]["dvs"]
                    if "{design_variable}" in raw_put_path
                    else (None,)
                )
                crs = (
                    ("historical", "future")
                    if "{climate_regime}" in raw_put_path
                    else (None,)
                )
                for dv in dvs:
                    for cr in crs:
                        update_result(
                            global_path(e, design_variable=dv, climate_regime=cr),
                            local_path(e, design_variable=dv, climate_regime=cr),
                        )

            return result

        # If we have no local configuration, initialize it with values from
        # the global app config.
        if (
            local_config_ts is None
            or local_config_ts < 0
            or local_config is None
        ):
            logger.debug(f"initializing local_config from config")
            return init_local_config(preserve_local=False)

        # If the local configuration is out of date, update it from the global
        # app config, preserving existing values of local config where possible.
        if path_get(local_config, "local_config.version") != path_get(
            config, "local_config.version"
        ):
            logger.debug(f"updating local_config from config")
            return init_local_config(preserve_local=True)

        ctx = dash.callback_context

        # Otherwise, one or more UI elements caused the change. Save those
        # in local_config.
        logger.debug("updating local config from UI change")
        local_config_output = local_config
        change = False
        for element, input_value in zip(
            updatable_ui_elements, updatable_ui_inputs
        ):
            if triggered_by(f'{element["id"]}.', ctx):
                change = True
                path_set(
                    local_config_output,
                    local_path(
                        element,
                        design_variable=design_variable,
                        climate_regime=climate_regime,
                    ),
                    input_value,
                )
        return local_config_output if change else dash.no_update

    # We wish to register callbacks programmatically, specifically, one for
    # each UI element defined in `updatable_ui_elements`. An example provided
    # in the `dcc.Store` documentation shows the registration of callbacks
    # in a loop like
    #
    #       for x in ...:
    #           @app.callback(...)
    #           def cb(...):
    #               ...
    #
    # That works correctly only if the callback function body `cb` does not use
    # the value of `x`. If it does use `x`, every callbacks uses the last value
    # of `x` in the loop due to closure semantics. Instead, you have to create a
    # function that closes over each value of `x` and register that function.
    def make_ui_update_callback(ui_element):
        """
        Make a callback that updates a UI element. Closes properly over
        argument ui_element.
        """

        def callback(
            local_config_ts, design_variable, climate_regime, local_config
        ):
            if not local_config_ts or local_config_ts < 0:
                return dash.no_update
            # if not any(
            #     v in local_path(ui_element)
            #     for v in ("design_variable", "climate_regime")
            # ):
            #     return dash.no_update
            return path_get(
                local_config,
                local_path(
                    ui_element,
                    design_variable=design_variable,
                    climate_regime=climate_regime,
                ),
            )

        return callback

    # Register callback for each UI element.
    for ui_element in updatable_ui_elements:
        app.callback(
            Output(ui_element["id"], ui_element["prop"]),
            Input("local_config", "modified_timestamp"),
            Input("design_variable", "value"),
            Input("climate_regime", "value"),
            State("local_config", "data"),
        )(make_ui_update_callback(ui_element))
