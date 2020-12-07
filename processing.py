from climpyrical.gridding import (
    flatten_coords,
    transform_coords,
    find_element_wise_nearest_pos,
)

import numpy as np

source_crs = {"init": "epsg:4326"}
target_crs = {
    "proj": "ob_tran",
    "o_proj": "longlat",
    "lon_0": -97,
    "o_lat_p": 42.5,
    "a": 6378137,
    "to_meter": 0.0174532925199,
    "no_defs": True,
}

def coord_prep(ds, df, station_dv, dv):
    
    rlon, rlat = ds.rlon.values, ds.rlat.values
    shape = ds[dv].values.shape#[1:]
    rlonx, rlaty = flatten_coords(rlon, rlat)
    lon, lat = transform_coords(
        rlonx, rlaty, source_crs=target_crs, target_crs=source_crs
    )

    lon = lon.reshape(shape)
    lat = lat.reshape(shape)
    station_value = np.ones(shape, dtype=object) * "No Station"

    ix, iy = find_element_wise_nearest_pos(
        rlon, rlat, df.rlon.values, df.rlat.values
    )
    station_value[iy, ix] = df[station_dv].values

    return lon, lat, station_value
