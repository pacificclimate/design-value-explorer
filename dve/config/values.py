from dve.dict_utils import path_get
import logging

logger = logging.getLogger(__name__)


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


def dv_roundto(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["roundto"]


def dv_colour_map(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime][
        "colour_map"
    ]


def dv_colour_scale_default(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["scale"][
        "default"
    ]


def dv_colour_scale_disable_logarithmic(
    config, design_variable, climate_regime
):
    return config["values"]["dvs"][design_variable][climate_regime][
        "scale"
    ].get("disable_logarithmic", False)


def dv_colour_bar_sigfigs(config, design_variable, climate_regime):
    return config["values"]["dvs"][design_variable][climate_regime]["colorbar"][
        "sigfigs"
    ]


def dv_historical_stations_column(config, design_variable):
    return config["values"]["dvs"][design_variable]["historical"]["datasets"][
        "stations"
    ]["column"]
