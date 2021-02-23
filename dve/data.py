from pkg_resources import resource_filename
from climpyrical.data import read_data
import pandas as pd


def load_file(path):
    print(f"Loading data from '{path}'")
    filename = resource_filename("dve", path)
    if path.endswith(".csv"):
        return pd.read_csv(filename)
    if path.endswith(".nc"):
        return read_data(filename)
    raise ValueError(f"Unrecognized file type in path '{path}'")


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
            "cmap": # value from config
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
    print(f"### Loading data from files.")
    data = {
        key: {
            "stations": load_file(value["station_path"]),
            "table": load_file(value["table"]),
            "model": load_file(value["input_model_path"]),
            "reconstruction": load_file(value["reconstruction_path"]),
            "station_dv": value["station_dv"],
            "cmap": value["cmap"],
        }
        for key, value in config["dvs"].items()
    }

    for key, value in data.items():
        (dv,) = value["model"].data_vars
        value["dv"] = dv

    return data
