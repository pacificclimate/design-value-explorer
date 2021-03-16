import os
import os.path
import csv
from dve.data import dv_value


dash_url_base_path = os.environ.get("DASH_URL_BASE_PATHNAME", "/")
download_by_location_dir = "downloads/by-location"


def download_filename(lon, lat, climate_regime):
    """
    Return a unique filename the download data for position lon, lat.

    :param lon:
    :param lat:
    :return: string
    """
    return f"dvs_{climate_regime}_{lon}_{lat}.csv"


def download_filepath(lon, lat, climate_regime, directory=download_by_location_dir):
    """
    Return a unique filepath for the download data for position lon, lat.
    :param lon:
    :param lat:
    :param climate_regime:
    :param directory: File directory containing files for downloading.
    :return: string
    """
    return os.path.join(directory, download_filename(lon, lat, climate_regime))


def download_base_url(
    base_path=dash_url_base_path,
    directory=download_by_location_dir,
):
    return os.path.join(base_path, directory)


def download_url(
    lon, lat, climate_regime, base_path=dash_url_base_path, directory=download_by_location_dir
):
    return os.path.join(base_path, download_filepath(lon, lat, climate_regime, directory))


def create_download_file(lon, lat, rlon, rlat, config, climate_regime):
    with open(os.path.join("/", download_filepath(lon, lat, climate_regime)), "w") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(("Latitude", lat))
        writer.writerow(("Longitude", lon))
        writer.writerow(tuple())

        if climate_regime == "historical":
            header_row = ("Model Value", "Reconstruction Value")
            dataset_ids = ("model", "reconstruction")
        else:
            header_row = tuple(config["future_change_factors"]["ids"])
            dataset_ids = tuple(config["future_change_factors"]["ids"])

        writer.writerow(("Design Value ID",) + header_row)
        for dv_id in config["dvs"].keys():
            writer.writerow(
                (dv_id,) +
                tuple(
                    float(
                        dv_value(
                            rlon,
                            rlat,
                            config,
                            dv_id,
                            climate_regime,
                            historical_dataset_id=dataset_id,
                            future_dataset_id=dataset_id,
                        )
                    )
                    for dataset_id in dataset_ids
                )
            )