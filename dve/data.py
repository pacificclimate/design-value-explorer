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
        f"get_data {(design_value_id, climate_regime, historical_dataset_id, future_dataset_id)}"
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
    logger.debug("dv_value: get_data")
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

