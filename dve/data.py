from pkg_resources import resource_filename
from climpyrical.data import read_data
import pandas as pd


def load_data(config):
    print(f"### Loading data from files.")
    data = {}
    for key in config["dvs"].keys():
        print(config["dvs"][key]["station_path"])
        info = {"stations": pd.read_csv(
            resource_filename(
                "dve",
                config["dvs"][key]["station_path"]
            )
        ),
            "model": read_data(
                resource_filename(
                    "dve",
                    config["dvs"][key]["input_model_path"]
                )
            ),
            "reconstruction": read_data(
                resource_filename(
                    "dve",
                    config["dvs"][key]["reconstruction_path"]
                )
            ),
            "station_dv": config["dvs"][key]["station_dv"],
            "table": pd.read_csv(
                resource_filename(
                    "dve",
                    config["dvs"][key]["table"]
                )
            ),
            "cmap": config["dvs"][key]["cmap"]
        }
        data[key] = info

    for key in data.keys():
        (dv, ) = data[key]["model"].data_vars
        data[key]["dv"] = dv

    return data
