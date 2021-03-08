from climpyrical.gridding import (
    flatten_coords,
    transform_coords,
    find_element_wise_nearest_pos,
)

import logging
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


def coord_prep(df, station_dv):

    if "longitude" in df.columns:
        df = df.rename(columns={"longitude": "lon"})
    if "Lon" in df.columns:
        df = df.rename(columns={"Lon": "lon"})
    if "Lat" in df.columns:
        df = df.rename(columns={"Lat": "lat"})
    if "long" in df.columns:
        df = df.rename(columns={"long": "lon"})
    if "latitude" in df.columns:
        df = df.rename(columns={"latitude": "lat"})
    if "name" in df.columns:
        df = df.rename(columns={"name": "station_name"})
    if "Name" in df.columns:
        df = df.rename(columns={"Name": "station_name"})
    if "prov" in df.columns:
        df = df.rename(columns={"prov": "province"})
    if "elev" in df.columns:
        df = df.rename(columns={"elev": "elev (m)"})
    if "elevation (m)" in df.columns:
        df = df.rename(columns={"elevation (m)": "elev (m)"})

    keys = ["lat", "lon"]
    contains_keys = [key not in df.columns for key in keys]
    if np.any(contains_keys):
        raise KeyError(f"Dataframe must contain {keys}")

    rkeys = ["rlat", "rlon"]
    contains_rkeys = [key not in df.columns for key in rkeys]
    if np.any(contains_rkeys):
        logging.info(
            "rlat or rlon not detected in input file."
            "converting assumes WGS84 coords to rotated pole"
        )
        nx, ny = transform_coords(df.lon.values, df.lat.values)
        df = df.assign(rlat=ny, rlon=nx)

    return df
