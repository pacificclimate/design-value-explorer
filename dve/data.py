"""
This module contains all the infrastructure for managing access to the data
(files) used by DVE.

The core of this module is the thread-safe caching of file objects. Because
Dash is multi-threaded, there can be concurrent requests for the same file,
and this can cause errors. The cache provides thread-safe mediation of file
access (and thread-safe access to itself, too, which is essential).

Two classes provide convenient thread-safe access to the two types
of file-data objects. They are structured very similarly and both use
(separate) thread safe caches to manage them. These classes also provide
thread-safe access to the data itself, which is probably unnecessary, since
all file access is conducted under the cache thread lock, forcing
serialization of access to *all* files. A more sophisticated approach to
cache invalidation (e.g., managing an "in-use" flag per cached item) would
provide for greater concurrency.

Finally, the perhaps too-generic `get_data` function uses the configuration
to turn convenient requests for data into actual file accesses, and  dispatches
these requests to the cached file objects.

TODO: Break this big file up into submodules: `Caching`, `DvXrDataset`,
  `PdCsvDataset`, and `get_data`.
TODO: Determine whether data access, which is read-only, needs thread locking.
TODO: `DvXrDataset`, `PdCsvDataset` have a very common structure. Factor this
  out into a base class factory.
"""

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
    - Is thread-safe. Access to cache itself is managed by a thread lock.
    - Is limited in size. When cache is full, a cache miss also causes an item
      to be evicted. At present, the algorithm is: evict a random item.
    - Invokes a user-supplied function when there is a cache miss to create
      the missing cached item (e.g., open a file).
    - Invokes a user-supplied function when there is cache eviction to perform
      finalization on the cached item before it is evicted (e.g., close a file).
    - *Yields* its result from within the cache thread lock to ensure that the
      cached item cannot be evicted by another cache request (and thus become
      unusable) while something is being done with it.
    """

    def __init__(self, name, on_miss, on_evict=None, maxsize=None):
        self.name = name
        self.on_miss = on_miss
        self.on_evict = on_evict
        self.maxsize = maxsize
        self._lock = threading.RLock()
        self._cache = {}

    def get(self, key):
        """
        A *generator* that yields the requested cache item.

        If the item is present in cache already, good. If the item is not,
        call `on_miss` to create it. If cache is full, Kick out a different
        cache item, calling `on_evict` on it.

        :param key: Cache key.
        :yield: Cached item.
        """
        logger.debug(f"{self.name} cache size: {len(self._cache)}")
        with self._lock:
            if key in self._cache:
                logger.debug(f"{self.name} cache hit: {key}")
                yield self._cache[key]

            if len(self._cache) > self.maxsize - 1:
                # Cache full.
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

            yield item


# Manage large DV datasets opened as `xarray.Dataset`s

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
    # `squeeze` drops any superfluous dimensions (i.e., dimensions of length 1,
    # e.g., time in the model dataset) from the data array.
    value = ds[dvds.dv_name].squeeze(drop=True).values[iy, ix]
    return lon, lat, value


# Cache event callbacks.

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
    Manager for design value datasets, more specifically NetCDF
    files full of design value rasters loaded as an xarray.Dataset.

    This class provides several services:
    1. Caches xarray.Datasets, opening and closing on cache miss and cache
       invalidation, respectively. Cache itself is thread-safe.
    2. Manages access to the datasets by a thread lock. Is this necessary?
    3. Provides a generic method for arbitrary operations that need to use
       a dataset.
    4. Provides methods for common operations (e.g., translation of rlonlat
       to lonlat coords).
    """
    CacheItem = namedtuple("CacheItem", "dataset lock")

    _cache = ThreadSafeCache(
        "DvXrDataset",
        on_miss=open_xr_dataset,
        on_evict=close_xr_dataset,
        maxsize = int(os.environ.get("LARGE_FILE_CACHE_SIZE", 20)),
    )

    def __init__(
        self,
        filepath,
        required_keys = ("rlat", "rlon", "lat", "lon")
    ):
        self.filepath = filepath
        self.required_keys = required_keys
        self.dv_name = self.apply(
            lambda dvds, ds: DvXrDataset.dv_name(ds, required_keys)
        )

    def apply(self, operation, *args, **kwargs):
        """
        Returns the result of an arbitrary operation performed on a dataset.
        Access to the dataset is managed via the thread lock; dataset is
        cached.

        :param operation: Operation to apply. Called with the following
          arguments: this object, the dataset, and any additional positional
          and keyword args provided.
        :param args: Positional args to pass to `operation`.
        :param kwargs: Keyword args to pass to `operation`.
        :return: Value returned by `operation`.
        """
        for access in DvXrDataset._cache.get(self.filepath):
            with access.lock:
                return operation(self, access.dataset, *args, **kwargs)

    def dv_values(self, x=None, y=None):
        """
        Get values accessed by index objects x and y.
        If x or y is None, return all values.
        """
        values = self.apply(dv_values)
        if x is None or y is None:
            return values
        return values[x, y]

    def lonlat_at_rlonlat(self, rlon, rlat):
        """
        Return lon, lat nearest specified rlon, rlat in dataset.
        """
        return self.apply(lonlat_at_rlonlat, rlon, rlat)

    def data_at_rlonlat(self, rlon, rlat):
        """
        Return data value nearest specified rlon, rlat in dataset.
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
    """
    Manager for data files loaded using `pandas.csv`, which returns a
    `pandas.DataFrame`.

    This class is very similar to, but somewhat simpler than, `DvXrDataset`.
    It uses a separate cache.
    """

    CacheItem = namedtuple("CacheItem", "data_frame lock")

    _cache = ThreadSafeCache(
        "PdCsvDataset",
        on_miss=open_pd_dataset,
        on_evict=close_pd_dataset,
        maxsize = int(os.environ.get("SMALL_FILE_CACHE_SIZE", 200)),
    )

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
        :param args: Positional args to pass to `operation`.
        :param kwargs: Keyword args to pass to `operation`.
        :return: Value returned by `operation`.
        """
        for access in PdCsvDataset._cache.get(self.filepath):
            with access.lock:
                return operation(self, access.dataset, *args, **kwargs)

    def data_frame(self):
        """Return the data frame loaded from the file."""
        return self.apply(lambda _, data_frame: data_frame)


def load_file(path):
    """Load files with appropriate class according to their type."""
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
    """
    Get a specific data object. This function knows the structure
    of `config` so that clients don't have to.
    """
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
