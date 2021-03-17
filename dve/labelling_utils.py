def dv_name(config, design_value_id):
    """
    Return the name of a design variable. Currently this is the internal
    id of the DV, so `config` is not used. That could conceivably change.
    """
    return design_value_id


def dv_units(config, design_value_id, climate_regime):
    """
    Return the units of a given design variable, for historical or future
    projections.
    """
    return config["dvs"][design_value_id][
        "abs_units" if climate_regime == "historical" else "cf_units"
    ]


def dv_label(
    config,
    design_value_id,
    climate_regime="historical",
    with_units=True,
    with_description=False,
):
    """
    Return the name, with optional description, and units of a DV.

    :param config:
    :param design_value_id:
    :param climate_regime:
    :param with_description:
    :return:
    """
    description = (
        f" [{config['dvs'][design_value_id]['description']}]"
        if with_description
        else ""
    )
    units = (
        f" ({dv_units(config, design_value_id, climate_regime)})"
        if with_units
        else ""
    )
    return f"{dv_name(config, design_value_id)}{description}{units}"


def climate_regime_label(config, climate_regime):
    return config["labels"]["climate_regime"][climate_regime]
