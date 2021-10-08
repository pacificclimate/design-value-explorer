"""
This module implements the mutual update relationship between local
preferences and the UI elements related to those preferences.

"Local preferences" means per-client preferences stored in
browser local storage. (Note: A "client" is a single instance of a web browser;
DVE does not provide for users with identities separate from browser instances,
nor the accompanying notions of signin etc.)

Local preferences include:

- Simple options (e.g., Mask, Stations, Grid), which are independent
  of DV and Period
- Per-DV/Period options (Colour Map, Scale, Num Colours)

When a client (web browser instance) first loads DVE, default settings for these
options are loaded from a global, client-independent configuration. Thereafter,
DVE uses the local preferences to manage these values: The app
sets the local preferences according to the user's selections of
these options in the UI. Conversely, when the app is reloaded by the same
client, the locally stored preferences are used to set the UI elements.
In addition, per-DV/Period UI elements are set to the local preference value
when either DV or Period is changed. This means
that the app remembers a user's preferences for how to view each dataset.

Implementation notes:

- Local preferences are stored using a `dcc.Store` layout element with
  id `"local_preferences"`.

- The mutual-update relationship between local preferences and the UI settings
  requires what Dash calls circular updates. Dash permits this only when the
  circularity is contained in a single callback; circularity due to two or more
  callbacks is forbidden in Dash. For more information, see
  https://dash.plotly.com/advanced-callbacks
  HOWEVER, it appears that our particular case evades that rule. I *think*
  the reason is that the local storage timestamp
  `Input("local_preferences", "modified_timestamp")`
  is a proxy for updates to the *data* in the local storage. Why this doesn't
  cause an infinite update loop is not clear to me, but it doesn't, and it
  simplifies the code.
  IF in future we get circularity problems, then the callbacks will have to be
  combined into one. The code gets uglier, but it's not terribly hard.

- There are some complications due to using `dcc.Store`: Specifically
  see "Retrieving the initial store data" in
  https://dash.plotly.com/dash-core-components/store . We follow that advice.

- To accommodate changes in the contents of local preferences (e.g., what options
  are managed by it, its layout), the global config value
  `local_preferences.version` is stored locally and compared on each load.
  If it differs, the local preferences is reloaded from global config,
  preserving local preferences settings if possible.
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
    Return the path for the value of a UI element in the local preferences.
    Return it raw (unsubstituted) if no kwargs are supplied, otherwise,
    substitute (string.format) the supplied kwargs in the raw path.
    """
    raw = element.get("local", element["global"])
    if len(kwargs) == 0:
        return raw
    return raw.format(**kwargs)


def show_stations(config, climate_regime=None, **kwargs):
    return climate_regime == "historical" and path_get(
        config, "ui.controls.stations.on"
    )


default_value_function = {"show_stations": show_stations}


def add(app, config):
    # These variables define the UI elements that mutually set and are set by
    # local preferences. To add a new UI element whose state is maintained in
    # local storage, add a new item to a list.
    updatable_ui_elements = path_get(config, "local_preferences.ui_elements")
    function_delimiter = path_get(config, "local_preferences.function_delimiter")

    @app.callback(
        Output("local_preferences", "data"),
        Input("local_preferences", "modified_timestamp"),
        *(Input(e["id"], e["prop"]) for e in updatable_ui_elements),
        State("local_preferences", "data"),
        State("design_variable", "value"),
        State("climate_regime", "value"),
    )
    def update_local_preferences(*args):
        # We have to unpack args like this because anything after a `*args` in
        # a method argument list is interpreted by Python as a keyword argument,
        # not a positional argument. So we can't just drop that in there.
        (
            local_preferences_ts,
            *updatable_ui_inputs,
            local_preferences,
            design_variable,
            climate_regime,
        ) = args
        logger.debug(f"update_local_preferences local_preferences_ts={local_preferences_ts}")

        # Helper
        def init_local_preferences(preserve_local=True):
            result = {}
            v_path = "local_preferences.version"
            path_set(result, v_path, path_get(config, v_path))

            def update_result(element, **kwargs):
                gpath = global_path(element, **kwargs)
                global_value = (
                    default_value_function[gpath[1:]](config, **kwargs)
                    if gpath.startswith(function_delimiter)
                    else path_get(config, gpath)
                )
                lpath = local_path(element, **kwargs)
                local_value = (
                    path_get(local_preferences, lpath, default=global_value)
                    if preserve_local
                    else global_value
                )
                path_set(result, lpath, local_value)

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
                        update_result(e, design_variable=dv, climate_regime=cr)

            return result

        # If we have no local preferences, initialize it with values from
        # the global app config.
        if (
            local_preferences_ts is None
            or local_preferences_ts < 0
            or local_preferences is None
        ):
            logger.debug(f"initializing local_preferences from config")
            return init_local_preferences(preserve_local=False)

        # If the local preferences is out of date, update it from the global
        # app config, preserving existing values of local preferences where
        # possible.
        if path_get(local_preferences, "local_preferences.version") != path_get(
            config, "local_preferences.version"
        ):
            logger.debug(f"updating local_preferences from config")
            return init_local_preferences(preserve_local=True)

        ctx = dash.callback_context

        # Otherwise, one or more UI elements caused the change. Save those
        # in local_preferences.
        logger.debug("updating local preferences from UI change")
        local_preferences_output = local_preferences
        change = False
        for element, input_value in zip(
            updatable_ui_elements, updatable_ui_inputs
        ):
            if triggered_by(f'{element["id"]}.', ctx):
                change = True
                path_set(
                    local_preferences_output,
                    local_path(
                        element,
                        design_variable=design_variable,
                        climate_regime=climate_regime,
                    ),
                    input_value,
                )
        return local_preferences_output if change else dash.no_update

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
            local_preferences_ts, design_variable, climate_regime, local_preferences
        ):
            if not local_preferences_ts or local_preferences_ts < 0:
                return dash.no_update
            # if not any(
            #     v in local_path(ui_element)
            #     for v in ("design_variable", "climate_regime")
            # ):
            #     return dash.no_update
            return path_get(
                local_preferences,
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
            Input("local_preferences", "modified_timestamp"),
            Input("design_variable", "value"),
            Input("climate_regime", "value"),
            State("local_preferences", "data"),
        )(make_ui_update_callback(ui_element))
