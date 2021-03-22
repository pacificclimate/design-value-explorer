import os
import functools
from collections import namedtuple
from random import randrange
import logging
import threading
from pkg_resources import resource_filename

import pandas as pd
import xarray

from climpyrical.data import check_valid_data, check_valid_keys

from dve.map_utils import rlonlat_to_rindices, rindices_to_lonlat


logger = logging.getLogger("dve")


# Operations for use with DvXrDataset.apply

def grid_size(dvds, ds):
    return ds.rlon.size, ds.rlat.size


def dv_values(dvds, ds):
    return ds[dvds.dv_name].values


def lonlat_at_rlonlat(dvds, ds, rlon, rlat):
    ix, iy = rlonlat_to_rindices(ds, rlon, rlat)
    lon, lat = rindices_to_lonlat(ds, ix, iy)
    return lon, lat


def data_at_rlonlat(dvds, ds, rlon, rlat):
    logger.debug(f"data_at_rlonlat{(dvds, ds, rlon, rlat)}")
    ix, iy = rlonlat_to_rindices(ds, rlon, rlat)
    lon, lat = rindices_to_lonlat(ds, ix, iy)
    value = ds[dvds.dv_name].values[ix, iy]
    logger.debug(f"data_at_rlonlat: return {(lon, lat, value)}")
    return lon, lat, value


class DvXrDataset:
    """
    Class that represents a design value dataset, more specifically a NetCDF
    file full of design value rasters loaded as an xarray.Dataset.

    This class provides several services:
    1. Caches xarray.Datasets, opening and closing on cache miss and cache
       invalidation, respectively
    2a. Manages access to the cache by a thread lock. This is essential to
        prevent simultaneous attempts to open the same uncached file, which
        causes crashes.
    2b. Manages access to the datasets by a thread lock. Is this necessary?
        All access to datasets at present is read only.
    3. Provides common operations (e.g., translation of rlonlat to lonlat
       coords) via methods.
    4. Provides a generic method for arbitrary operations that need to use
       a dataset.
    """

    # Cache of xarray.Dataset and corresponding lock for file access,
    # keyed by filepath
    # TODO: Abstract this as a separate class? But why? It's a singleton.
    #   One reason: Easier to manage cache size.
    _cache_lock = threading.RLock()
    _cache = {}
    _cache_size = int(os.environ.get("FILE_CACHE_SIZE", 20))
    CacheItem = namedtuple("CacheItem", "dataset lock")

    @classmethod
    def get_access(cls, filepath):
        with cls._cache_lock:
            if filepath in cls._cache:
                logger.debug(f"cache hit: {filepath}")
                return cls._cache[filepath]

            # Create a new item and add it to the cache
            logger.debug(f"cache miss: {filepath}")
            lock = threading.RLock()
            with lock:
                dataset = xarray.open_dataset(filepath)
                access = cls.CacheItem(dataset, lock)
                cls._cache[filepath] = access

            if len(cls._cache) > cls._cache_maxsize:
                # Cache bound exceeded.
                # Kick a random item out of cache. This is simpler than LRU and
                # sufficient for testing.
                # Note: Essential to close dataset before kicking out.
                rand_key = tuple(cls._cache.keys())[randrange(0, cls._cache_maxsize)]
                logger.debug(f"cache eviction: {rand_key}")
                cls._cache[rand_key].dataset.close()
                del cls._cache[rand_key]

            return access

    def __init__(
        self,
        filepath,
        required_keys = ("rlat", "rlon", "lat", "lon")
    ):
        self.filepath = filepath
        self.required_keys = required_keys
        access = DvXrDataset.get_access(filepath)
        with access.lock:
            self.dv_name = DvXrDataset.dv_name(access.dataset, required_keys)

    def apply(self, operation, *args, **kwargs):
        """
        Returns the result of an arbitrary operation performed on a dataset.
        Access to the dataset is managed via the thread lock; dataset is
        cached.

        :param operation: Operation to apply. Called with the following
          arguments: this object, the dataset, and any additional positional
          and keyword args provided.
        :param args:
        :param kwargs:
        :return:
        """
        access = DvXrDataset.get_access(self.filepath)
        with access.lock:
            return operation(self, access.dataset, *args, **kwargs)

    def dv_values(self, x=None, y=None):
        """
        Get values accessed by x and y. If x or y is None, return all values.

        :param x:
        :param y:
        :return:
        """
        values = self.apply(dv_values)
        if x is None or y is None:
            return values
        return values[x, y]

    def lonlat_at_rlonlat(self, rlon, rlat):
        """
        Return lon, lat nearest specified rlon, rlat in dataset.

        :param rlon:
        :param rlat:
        :return:
        """
        return self.apply(lonlat_at_rlonlat, rlon, rlat)

    def data_at_rlonlat(self, rlon, rlat):
        """
        Return data value nearest specified rlon, rlat in dataset.

        :param rlon:
        :param rlat:
        :return:
        """
        return self.apply(data_at_rlonlat, rlon, rlat)

    # TODO: This needn't be a method of this class.
    @classmethod
    def dv_name(cls, ds, required_keys):
        # Note: where d is a dict, set(d) == set(d.keys())
        all_keys = set(ds.variables).union(set(ds.dims))

        check_valid_keys(all_keys, required_keys)
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
        rv = DvXrDataset(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    raise ValueError(f"Unrecognized file type in path '{path}'")


# @functools.lru_cache(maxsize=int(os.environ.get("FILE_CACHE_SIZE", 50)))
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
    # logger.debug(f"get_data: cache info: {load_file_cached.cache_info()}")
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
    dataset = get_data(
        config,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    )
    data = dataset.data_at_rlonlat(rlon, rlat)
    logger.debug(f"dv_value: data = {data}")
    return data[2]
    # ix, iy = rlonlat_to_rindices(data, rlon, rlat)
    # return data.dv.values[iy, ix]
