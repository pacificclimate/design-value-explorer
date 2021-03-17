import os
import functools
import logging
from pkg_resources import resource_filename
from climpyrical.data import read_data
import pandas as pd
from dve.map_utils import rlonlat_to_rindices

logger = logging.getLogger("dve")


def load_file(path):
    logger.info(f"Loading data from '{path}'")
    filename = resource_filename("dve", path)
    if path.endswith(".csv"):
        rv = pd.read_csv(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    if path.endswith(".nc"):
        rv = read_data(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    raise ValueError(f"Unrecognized file type in path '{path}'")


@functools.lru_cache(maxsize=int(os.environ.get("FILE_CACHE_SIZE", 50)))
def load_file_cached(filepath):
    """Caches the results of a load_file operation. This is the basis of
    all on-demand data retrieval.
    TODO: Replace this by applying caching directly to `load_file`.
    """
    return load_file(filepath)


def get_data(
    config,
    design_value_id,
    climate_regime,
    historical_dataset_id=None,
    future_dataset_id=None,
):
    """Get a specific data object. This function knows the structure
    of `config` so that clients don't have to."""
    logger.debug(
        f"### get_data {(design_value_id, climate_regime, historical_dataset_id, future_dataset_id)}"
    )
    if climate_regime == "historical":
        path_key = {
            "stations": "station_path",
            "table": "table",
            "model": "input_model_path",
            "reconstruction": "reconstruction_path",
        }[historical_dataset_id]
        return load_file_cached(config["dvs"][design_value_id][path_key])
    return load_file_cached(
        config["dvs"][design_value_id]["future_change_factor_paths"][
            future_dataset_id
        ]
    )


def load_data(config):
    """
    Load all data used by the app.

    The loading process maps `config` to a data dict as follows:

    {
        key: {
            "stations": # dict of CSV read from "station_path"
            "table": # dict of CSV read from "table"
            "model": # climpyrical data object read from "input_model_path"
            "reconstruction": # climpyrical data object read from "reconstruction_path"
            "station_dv": # value from config
            "colour_map": # value from config
            "dv":  # 'data_vars' value from model data (possible problem)
        }
        for key, value in config["dvs"].items()
    }

    This is extremely slow, and places a lot of data in memory that are likely
    not needed at any one time. In particular, I think, the data under "model"
    and "reconstruction" (a) are bulky and (b) do not need to be preloaded.

    Plan: Find places in code where data["reconstruction"] and data["model"]
    are used, and replace them with memoized `get` functions that load the data
    on demand. If this is possible ... we have to watch out for how
    data[key]["dv"] is used ... maybe it can be lazy loaded, maybe not.
    """
    logger.info(f"Loading data from files.")
    data = {
        key: {
            "stations": load_file(value["station_path"]),
            "table": load_file(value["table"]),
            "model": load_file(value["input_model_path"]),
            "reconstruction": load_file(value["reconstruction_path"]),
            "station_dv": value["station_dv"],
            "colour_map": value["colour_map"],
        }
        for key, value in config["dvs"].items()
    }
    logger.info("Data loaded")

    for key, value in data.items():
        (dv,) = value["model"].data_vars
        value["dv"] = dv

    return data


def dv_value(
    rlon,
    rlat,
    config,
    design_value_id,
    climate_regime,
    historical_dataset_id=None,
    future_dataset_id=None,
):
    """
    Get a design variable value for a specified lonlat in rotated pole
    coordinates.
    """
    data = get_data(
        config,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    )
    (dv_var_name,) = data.data_vars
    ix, iy = rlonlat_to_rindices(data, rlon, rlat)
    return data[dv_var_name].values[iy, ix]

