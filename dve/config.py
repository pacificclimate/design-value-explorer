"""
This module simplifies and abstracts out accessing values from the
configuration. Not all config access uses these functions, but the gnarly
cases are centralized here.
"""

import os.path
import logging
from pkg_resources import resource_filename
from dve.dict_utils import path_get


logger = logging.getLogger(__name__)


def file_exists(filepath):
    filepath = resource_filename("dve", filepath)
    return os.path.isfile(filepath)


def validate_filepath(filepath):
    if not file_exists(filepath):
        logger.warning(f"'{filepath}' does not exist or is not a file")


def validate_config(config, cfg_path, log=logger.warning, **kwargs):
    """
    Validate the config addressed by `cfg_path`. If there is nothing at the
    specified path in the config object, log this fact. Otherwise validate
    the filepath found at that path.
    """
    filepath = path_get(config, cfg_path, **kwargs)
    if filepath is None:
        log(f"Expected config at '{cfg_path}' is not present.")
    else:
        validate_filepath(filepath)


def validate(config):
    """
    Validate a configuration. Specifically:
    - Check that all filepaths specified in config exist. Log a warning message
      for those which do not exist.
    """
    for filepath in config["values"]["paths"].values():
        validate_filepath(filepath)

    for design_variable in config["values"]["ui"]["dvs"]:

        # Validate historical filepaths, if present
        cfg_base_path = f"dvs/{design_variable}/historical/datasets"
        if path_get(config, cfg_base_path, separator="/") is None:
            logger.info(
                f"No historical datasets specified for {design_variable}"
            )
        else:
            for cfg_ext_path in (
                "model",
                "reconstruction",
                "stations/path",
                "table_C2",
            ):
                validate_config(
                    config, f"{cfg_base_path}/{cfg_ext_path}", separator="/"
                )

        # Validate future filepaths, if present.
        cfg_base_path = f"dvs/{design_variable}/future/datasets"
        if path_get(config, cfg_base_path, separator="/") is None:
            logger.info(f"No future datasets specified for {design_variable}")
        else:
            for cfg_ext_path in config["values"]["ui"]["future_change_factors"]:
                validate_config(
                    config, f"{cfg_base_path}/{cfg_ext_path}", separator="/"
                )


def filepath_for(
    config,
    design_variable,
    climate_regime,
    historical_dataset_id=None,
    future_dataset_id=None,
):
    root_path = f"values/dvs/{design_variable}/{climate_regime}/datasets"

    if climate_regime == "historical":
        ext_path = {
            "stations": "stations/path",
            "table": "table_C2",
            "model": "model",
            "reconstruction": "reconstruction",
        }[historical_dataset_id]
    else:
        ext_path = future_dataset_id

    return path_get(config, f"{root_path}/{ext_path}", separator="/")


def filepath_defined(*args, **kwargs):
    return filepath_for(*args, **kwargs) is not None


def dv_has_climate_regime(config, design_variable, climate_regime):
    """
    Return a boolean indicating whether a DV has definitions for specific
    climate regime (historical or future) datasets.
    """
    return climate_regime in config["values"]["dvs"][design_variable]


def dv_name(config, lang, design_variable):
    """
    Return the name of a design variable. Currently this is the internal
    id of the DV, so `config` and `lang` are not used. 
    That could conceivably change.
    """
    return design_variable


def dv_tier(config, design_variable):
    return config["values"]["dvs"][design_variable]["tier"]


def nice_units(config, units):
    try:
        definition = config["values"]["units"][units]
        return (
            definition["nice"],
            (" " if definition.get("separator", True) else ""),
        )
    except KeyError:
        return units, " "


def units_suffix(units, pattern=" ({units})"):
    if units is None or units == "":
        return ""
    return pattern.format(units=units)


def dv_units(config, design_variable, climate_regime, nice=True):
    """
    Return the units of a given design variable, for historical or future
    projections.
    """
    units = config["values"]["dvs"][design_variable][climate_regime]["units"]
    if not nice:
        return units
    return nice_units(config, units)[0]


def dv_label(
    config, lang,
    design_variable,
    climate_regime="historical",
    with_units=True,
    with_description=False,
):
    """
    Return the name, with optional description, and units of a DV.
    """
    description = (
        f" {config['text']['labels'][lang]['dvs'][design_variable]['description']}"
        if with_description
        else ""
    )
    units = (
        units_suffix(dv_units(config, design_variable, climate_regime))
        if with_units
        else ""
    )
    return f"{dv_name(config, lang, design_variable)}{description}{units}"


def dv_roundto(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["roundto"]


def dv_colour_map(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["colour_map"]


def dv_colour_scale_default(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["scale"]["default"]


def dv_colour_scale_disable_logarithmic(
    config, design_variable, climate_regime
):
    return config["values"]["dvs"][design_variable][climate_regime]["scale"].get(
        "disable_logarithmic", False
    )


def dv_colour_bar_sigfigs(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["colorbar"]["sigfigs"]


def dv_historical_stations_column(config, design_variable):
    return config["values"]["dvs"][design_variable]["historical"]["datasets"]["stations"][
        "column"
    ]


# Text(ish)

def app_title(config, lang):
    return config["text"]["labels"][lang]["app_title"]


def dv_dropdown_label(config, lang):
    return config["text"]["labels"][lang]["dv_dropdown"]


def dv_dropdown_options(config, lang):
    return [
        {
            "label": dv_label(
                config, lang,
                design_variable,
                with_units=False,
                with_description=True,
            ),
            "value": design_variable,
        }
        for design_variable in config["values"]["ui"]["dvs"]
    ]


def climate_regime_label(config, lang, climate_regime, which="long"):
    return config["text"]["labels"][lang]["climate_regime"][climate_regime][which]


def historical_dataset_label(config, lang, dataset_id):
    return config["text"]["labels"][lang]["historical_dataset"][dataset_id]


def interpolation_value_label(config, lang):
    return config["text"]["labels"][lang]["interpolation"]


def future_change_factor_label(config, lang, dataset_id, which="short", nice=True):
    units, separator = nice_units(config, "degC") if nice else ("degC", " ")
    return config["text"]["labels"][lang]["future_change_factors"][which].format(
        value=dataset_id, separator=separator, units=units
    )


def download_table_label(config, lang, column):
    return config["text"]["labels"][lang]["download_table"][column]


def dataset_label(
    config, lang,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
    which="short",
    nice=True,
):
    if climate_regime == "historical":
        return historical_dataset_label(config, lang, historical_dataset_id)
    return future_change_factor_label(
        config, lang, future_dataset_id, which=which, nice=nice
    )


def map_title(
    config, lang,
    design_variable,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
):
    dl = dataset_label(
        config, lang,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        which="short",
        nice=True,
    )
    dataset = "" if climate_regime == "historical" else f" ({dl})"
    return config["text"]["labels"][lang]["map"]["title"][climate_regime].format(
        dv=dv_label(
            config, lang, design_variable, climate_regime, with_description=True
        ),
        tier=dv_tier(config, design_variable),
        climate_regime=climate_regime_label(
            config, lang, climate_regime, which="short"
        ),
        dataset=dataset,
    )


def climate_regime_ctrl_options(config, lang, which="long"):
    return [
        {
            "label": config["text"]["labels"][lang]["climate_regime"][cr][which],
            "value": cr,
        }
        for cr in ("historical", "future")
    ]


def overlay_options_section_title(config, lang):
    return config["text"]["labels"][lang]["overlay-options"]["title"]


def overlay_options_control_columns(config, lang):
    columns = config["text"]["labels"][lang]["overlay-options"]["columns"]
    return [(column["title"], column["width"]) for column in columns]


def overlay_options_stations_label(config, lang):
    # TODO: This will need some fixing for multilang; poss do like
    #  colorscale-options
    return "(HISTORICAL ONLY)"


def color_map_ctrl_options(config, lang):
    return [{"value": x, "label": x} for x in config["values"]["map"]["colour_maps"]]


def scale_ctrl_options(config, lang):
    # TODO: Put into config
    return [
        {"label": "Linear", "value": "linear"},
        {"label": "Logarithmic", "value": "logarithmic"},
    ]


def colourbar_options_section_title(config, lang):
    return config["text"]["labels"][lang]["colorscale-options"]["title"]


def color_bar_options_ctrl_title(config, lang, col_key):
    return (
        config["text"]["labels"][lang]["colorscale-options"]["columns"][col_key][
            "title"
        ],
    )


def color_bar_options_ctrl_width(config, lang, col_key):
    return (
        config["text"]["labels"][lang]["colorscale-options"]["columns"][col_key][
            "width"
        ],
    )


def map_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["map-tab"]


def table_c2_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["table-tab"]


def help_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["help-tab"]


def help_subtab_label(config, lang, index):
    return config["text"]["help"]["tabs"][lang][index]["label"]


def help_subtab_content(config, lang, index):
    return config["text"]["help"]["tabs"][lang][index]["content"]


def about_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["about-tab"]


def about_subtab_label(config, lang, index):
    return config["text"]["about"]["tabs"][lang][index]["label"]


def about_subtab_card_spec(config, lang, index):
    # TODO: This will need some extra effort for multilang
    return config["text"]["about"]["tabs"][lang][index]["cards"]


def table_c2_title(config, lang, design_variable):
    return config["text"]["labels"][lang]["table_C2"]["title"].format(
        name=dv_name(config, lang, design_variable),
        tier=dv_tier(config, design_variable),
        name_and_units=dv_label(
            config, lang, design_variable, climate_regime="historical"
        ),
    )


def table_c2_no_table_data_msg(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["no_table_data_error"]


def table_c2_no_station_data_msg(config, lang, design_variable):
    return config["text"]["labels"][lang]["table_C2"]["no_station_data"].format(
        design_variable
    )


def table_c2_location_label(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["location"]


def table_c2_province_label(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["province"]


def table_c2_longitude_label(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["longitude"]


def table_c2_latitude_label(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["latitude"]
