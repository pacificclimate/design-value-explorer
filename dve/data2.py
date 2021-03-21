import os
import functools
import logging
from pkg_resources import resource_filename

import pandas as pd
import xarray

from climpyrical.data import check_valid_data, check_valid_keys

from dve.map_utils import rlonlat_to_rindices


logger = logging.getLogger("dve")


class DvDataset:
    def __init__(
        self,
        filepath,
        required_keys = ("rlat", "rlon", "lat", "lon")
    ):
        self.required_keys = required_keys
        ds = xarray.open_dataset(filepath)
        self.ds = ds
        for name in required_keys:
            setattr(self, name, getattr(ds, name))
        self.dv = getattr(ds, self.dv_name())

    def dv_name(self):
        ds = self.ds
        # Note: where d is a dict, set(d) == set(d.keys())
        all_keys = set(ds.variables).union(set(ds.dims))

        check_valid_keys(all_keys, self.required_keys)
        check_valid_data(ds)

        # keys with size > 2 are good, otherwise
        # are superfluous (time, time_bnds, rotated_pole, etc)
        extra_keys = [key for key in all_keys if ds[key].size <= 2]

        # check how many data variables with
        # size > 2 are remaining. If more than one
        # raise error as we can't distinguish from
        # the intended variable.
        dv = set(ds.data_vars) - set(extra_keys)
        if len(dv) != 1:
            raise KeyError(
                "Too many data variables detected."
                f"Found {dv}, please remove the"
                "field that is not of interest."
            )
        (dv,) = dv
        return dv


def load_file(path):
    logger.info(f"Loading data from '{path}'")
    filename = resource_filename("dve", path)
    if path.endswith(".csv"):
        rv = pd.read_csv(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    if path.endswith(".nc"):
        rv = DvDataset(filename)
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
        file = load_file_cached(config["dvs"][design_value_id][path_key])
    else:
        file = load_file_cached(
            config["dvs"][design_value_id]["future_change_factor_paths"][
                future_dataset_id
            ]
        )
    logger.debug(f"get_data: cache info: {load_file_cached.cache_info()}")
    return file


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
    ix, iy = rlonlat_to_rindices(data, rlon, rlat)
    return data.dv.values[iy, ix]
