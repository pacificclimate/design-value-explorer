"""
This module simplifies and abstracts out accessing values from the
configuration. Not all config access uses these functions, but the gnarly
cases are centralized here.
"""

import os.path
import logging
from pkg_resources import resource_filename
from dve.dict_utils import path_get


logger = logging.getLogger("dve")


def file_exists(filepath):
    filepath = resource_filename("dve", filepath)
    return os.path.isfile(filepath)


def validate_filepath(filepath):
    if not file_exists(filepath):
        logger.warning(f"'{filepath}' does not exist or is not a file")


def validate_config(config, cfg_path, log=logger.warning, **kwargs):
    # logger.debug(f"Validating '{cfg_path}'")
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
    for filepath in config["paths"].values():
        validate_filepath(filepath)

    for design_variable in config["ui"]["dvs"]:

        # Validate historical filepaths, if present
        if dv_has_climate_regime(config, design_variable, "historical"):
            cfg_base_path = f"dvs/{design_variable}/historical/datasets"
            for cfg_ext_path in (
                "model",
                "reconstruction",
                "stations/path",
                "table_C2",
            ):
                validate_config(
                    config, f"{cfg_base_path}/{cfg_ext_path}", separator="/"
                )

        # Validate future filepaths. These must always be present.
        cfg_base_path = f"dvs/{design_variable}/future/datasets"
        for cfg_ext_path in config["ui"]["future_change_factors"]:
            validate_config(
                config, f"{cfg_base_path}/{cfg_ext_path}", log=logger.error, separator="/"
            )


def filepath_for(
    config,
    design_variable,
    climate_regime,
    historical_dataset_id=None,
    future_dataset_id=None,
):
    root_path = f"dvs/{design_variable}/{climate_regime}/datasets"

    if climate_regime == "historical":
        ext_path = {
            "stations": "stations/path",
            "table": "table_C2",
            "model": "model",
            "reconstruction": "reconstruction",
        }[historical_dataset_id]
    else:
        ext_path = future_dataset_id

    return path_get(config, f"{root_path}/{ext_path}", separator='/')


def filepath_defined(*args, **kwargs):
    return filepath_for(*args, **kwargs) is not None


def dv_has_climate_regime(config, design_variable, climate_regime):
    """
    Return a boolean indicating whether a DV has definitions for specific
    climate regime (historical or future) datasets.
    """
    return climate_regime in config["dvs"][design_variable]


def dv_name(config, design_variable):
    """
    Return the name of a design variable. Currently this is the internal
    id of the DV, so `config` is not used. That could conceivably change.
    """
    return design_variable


def nice_units(config, units):
    try:
        definition = config["units"][units]
        return (
            definition["nice"],
            (" " if definition.get("separator", True) else ""),
        )
    except KeyError:
        return units, " "


def dv_units(config, design_variable, climate_regime, nice=True):
    """
    Return the units of a given design variable, for historical or future
    projections.
    """
    units = config["dvs"][design_variable][climate_regime]["units"]
    if not nice:
        return units
    return nice_units(config, units)[0]


def dv_label(
    config,
    design_variable,
    climate_regime="historical",
    with_units=True,
    with_description=False,
):
    """
    Return the name, with optional description, and units of a DV.
    """
    description = (
        f" {config['dvs'][design_variable]['description']}"
        if with_description
        else ""
    )
    units = (
        f" ({dv_units(config, design_variable, climate_regime)})"
        if with_units
        else ""
    )
    return f"{dv_name(config, design_variable)}{description}{units}"


def dv_roundto(config, design_variable, climate_regime):
    return config["dvs"][design_variable][climate_regime]["roundto"]


def dv_colour_map(config, design_variable, climate_regime):
    return config["dvs"][design_variable][climate_regime]["colour_map"]


def dv_colour_scale_default(config, design_variable, climate_regime):
    return config["dvs"][design_variable][climate_regime]["scale"]["default"]


def dv_colour_scale_disable_logarithmic(
    config, design_variable, climate_regime
):
    return config["dvs"][design_variable][climate_regime]["scale"].get(
        "disable_logarithmic", False
    )


def dv_colour_bar_sigfigs(config, design_variable, climate_regime):
    return config["dvs"][design_variable][climate_regime]["colorbar"]["sigfigs"]


def dv_historical_stations_column(config, design_variable):
    return config["dvs"][design_variable]["historical"]["datasets"]["stations"][
        "column"
    ]


def climate_regime_label(config, climate_regime, which="long"):
    return config["ui"]["labels"]["climate_regime"][climate_regime][which]


def historical_dataset_label(config, dataset_id):
    return config["ui"]["labels"]["historical_dataset"][dataset_id]


def future_change_factor_label(config, dataset_id, which="short", nice=True):
    units, separator = nice_units(config, "degC") if nice else ("degC", " ")
    return config["ui"]["labels"]["future_change_factors"][which].format(
        value=dataset_id, separator=separator, units=units
    )


def dataset_label(
    config,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
    which="short",
    nice=True,
):
    if climate_regime == "historical":
        return historical_dataset_label(config, historical_dataset_id)
    return future_change_factor_label(
        config, future_dataset_id, which=which, nice=nice
    )


def map_title(
    config,
    design_variable,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
):
    dl = dataset_label(
        config,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        which="short",
        nice=True,
    )
    dataset = "" if climate_regime == "historical" else f" ({dl})"
    return config["ui"]["labels"]["map"]["title"].format(
        dv=dv_label(
            config, design_variable, climate_regime, with_description=True
        ),
        climate_regime=climate_regime_label(
            config, climate_regime, which="short"
        ),
        dataset=dataset,
    )
