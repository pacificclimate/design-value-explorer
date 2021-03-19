import os.path
from pkg_resources import resource_filename


def validate_filepath(filepath):
    filepath = resource_filename("dve", filepath)
    if not os.path.isfile(filepath):
        raise ValueError(f"'{filepath}' does not exist or is not a file")


def validate(config):
    """
    Validate a configuration. Specifically:
    - Check that all filepaths in use exist

    Raise a descriptive exception if validation fails.
    """
    for filepath in config["paths"].values():
        validate_filepath(filepath)

    for dv_id in config["ui"]["dvs"]:
        dv_defn = config["dvs"][dv_id]

        if dv_has_historical(config, dv_id):
            for key in (
                "station_path",
                "input_model_path",
                "reconstruction_path",
                "table",
            ):
                validate_filepath(dv_defn[key])

        for fcf_id in config["ui"]["future_change_factors"]:
            validate_filepath(dv_defn["future_change_factor_paths"][fcf_id])


# TODO: Deprecated
def dv_has_historical(config, design_value_id):
    return dv_has_climate_regime(config, design_value_id, "historical")


def dv_has_climate_regime(config, design_value_id, climate_regime):
    """
    Return a boolean indicating whether a DV has definitions for specific
    climate regime (historical or future) datasets.
    """
    return (
        "abs_units" if climate_regime == "historical" else "cf_units"
    ) in config["dvs"][design_value_id]
