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


class ThreadSafeCache:
    """
    A cache which:
    - Is thread-safe. Access to cache is managed by a thread lock.
    - Is limited in size. When cache is full, a cache miss also causes an item
      to be evicted. At present, the algorithm is: evict a random item.
    - Invokes a user-supplied function when there is a cache miss to create
      the missing cached item (e.g., open a file).
    - Invokes a user-supplied function when there is cache eviction to perform
      finalization on the cached item before it is evicted (e.g., close a file).
    """

    def __init__(self, name, on_miss, on_evict=None, maxsize=None):
        self.name = name
        self.on_miss = on_miss
        self.on_evict = on_evict
        self.maxsize = maxsize
        self._lock = threading.RLock()
        self._cache = {}

    def get(self, key):
        logger.debug(f"{self.name} cache size: {len(self._cache)}")
        with self._lock:
            if key in self._cache:
                logger.debug(f"{self.name} cache hit: {key}")
                return self._cache[key]

            if len(self._cache) > self.maxsize - 1:
                # Cache bound exceeded.
                # Kick a random item out of cache. This is simpler than LRU and
                # sufficient for testing, and even probably for production.
                rand_key = tuple(self._cache.keys())[randrange(0, self.maxsize)]
                logger.debug(f"cache eviction: {rand_key}")
                if self.on_evict is not None:
                    self.on_evict(key, self._cache[rand_key])
                del self._cache[rand_key]

            # Create a new item and add it to the cache
            logger.debug(f"{self.name} cache miss: {key}")
            item = self.on_miss(key)
            self._cache[key] = item

            return item


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
    ix, iy = rlonlat_to_rindices(ds, rlon, rlat)
    lon, lat = rindices_to_lonlat(ds, ix, iy)
    # logger.debug(f"{ds[dvds.dv_name]}")
    # `squeeze` drops any superfluous dimensions (i.e., dimensions of length 1,
    # e.g., time in the model dataset) from the data array.
    value = ds[dvds.dv_name].squeeze(drop=True).values[iy, ix]
    return lon, lat, value


# Manage large DV datasets opened as `xarray.Dataset`s

def open_xr_dataset(filepath):
    lock = threading.RLock()
    with lock:
        dataset = xarray.open_dataset(filepath)
        return DvXrDataset.CacheItem(dataset, lock)


def close_xr_dataset(filepath, access):
    with access.lock:
        access.dataset.close()


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
    CacheItem = namedtuple("CacheItem", "dataset lock")

    _cache = ThreadSafeCache(
        "DvXrDataset",
        on_miss=open_xr_dataset,
        on_evict=close_xr_dataset,
        maxsize = int(os.environ.get("LARGE_FILE_CACHE_SIZE", 20)),
    )

    @classmethod
    def get_access(cls, filepath):
        return cls._cache.get(filepath)

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


# Manage small CSV datasets opened as `pandas.csv`s

def open_pd_dataset(filepath):
    lock = threading.RLock()
    with lock:
        data_frame = pd.read_csv(filepath)
        return DvXrDataset.CacheItem(data_frame, lock)


# TODO: This may not be necessary.
def close_pd_dataset(filepath, access):
    # Free the data frame.
    access.data_frame = None


class PdCsvDataset:
    CacheItem = namedtuple("CacheItem", "data_frame lock")

    _cache = ThreadSafeCache(
        "PdCsvDataset",
        on_miss=open_pd_dataset,
        on_evict=close_pd_dataset,
        maxsize = int(os.environ.get("SMALL_FILE_CACHE_SIZE", 200)),
    )

    @classmethod
    def get_access(cls, filepath):
        return cls._cache.get(filepath)

    def __init__(self, filepath):
        self.filepath = filepath

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
        access = PdCsvDataset.get_access(self.filepath)
        with access.lock:
            return operation(self, access.dataset, *args, **kwargs)

    def data_frame(self):
        return self.apply(lambda _, data_frame: data_frame)


def load_file(path):
    logger.info(f"Loading data from '{path}'")
    filename = resource_filename("dve", path)
    if path.endswith(".csv"):
        rv = PdCsvDataset(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    if path.endswith(".nc"):
        rv = DvXrDataset(filename)
        logger.debug(f"Loaded data from '{path}'")
        return rv
    raise ValueError(f"Unrecognized file type in path '{path}'")


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
        file = load_file(config["dvs"][design_value_id][path_key])
    else:
        file = load_file(
            config["dvs"][design_value_id]["future_change_factor_paths"][
                future_dataset_id
            ]
        )
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
    dataset = get_data(
        config,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    )
    data = dataset.data_at_rlonlat(rlon, rlat)
    return data[2]
    # ix, iy = rlonlat_to_rindices(data, rlon, rlat)
    # return data.dv.values[iy, ix]
