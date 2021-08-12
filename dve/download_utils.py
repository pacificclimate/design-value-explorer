import os
import os.path
import csv
from dve.config import dv_has_climate_regime
from dve.data import dv_value
from dve.config import dv_units, dv_roundto, future_change_factor_label
from dve.math_utils import round_to_multiple


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


def download_filepath(
    lon, lat, climate_regime, directory=download_by_location_dir
):
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
    base_path=dash_url_base_path, directory=download_by_location_dir
):
    return os.path.join(base_path, directory)


def download_url(
    lon,
    lat,
    climate_regime,
    base_path=dash_url_base_path,
    directory=download_by_location_dir,
):
    return os.path.join(
        base_path, download_filepath(lon, lat, climate_regime, directory)
    )


def get_download_data(
    rlon, rlat, config, climate_regime, historical_dataset_id, future_dataset_id
):
    """
    Return the data used to populate a download table. This data is used to
    populate two different items (the UI display and the download file), and
    this function makes it possible to marshal that data only once.
    Reason: Repeated marshalling of the same data may be causing a difficult to
    diagnose crash. This is an attempt to test that hypothesis and prevent the
    crash.

    :return: sequence of
        (row ids) seq of design_variables
        (column ids) seq of dataset_ids
        (data) seq of data rows, matched to row ids;
            each data row is a sequence of data values, matched to column ids.
    """
    # Row ids
    design_variables = tuple(
        dv_id
        for dv_id in config["ui"]["dvs"]
        if dv_has_climate_regime(config, dv_id, climate_regime)
    )

    # Column ids
    if climate_regime == "historical":
        dataset_ids = ("reconstruction",)
    else:
        dataset_ids = tuple(config["ui"]["future_change_factors"])

    # Data
    data_values = tuple(
        tuple(
            float(
                dv_value(
                    rlon,
                    rlat,
                    config,
                    design_variable,
                    climate_regime,
                    historical_dataset_id=dataset_id,
                    future_dataset_id=dataset_id,
                )
            )
            for dataset_id in dataset_ids
        )
        for design_variable in design_variables
    )

    return design_variables, dataset_ids, data_values


def create_download_file(
    lon, lat, config, climate_regime, design_variables, dataset_ids, data_values
):
    with open(
        os.path.join("/", download_filepath(lon, lat, climate_regime)), "w"
    ) as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(("Latitude", lat))
        writer.writerow(("Longitude", lon))
        writer.writerow(tuple())

        if climate_regime == "historical":
            # TODO: These label(s) should be defined in config
            # value_headers = tuple(
            #     f"{dataset_id.capitalize()}" for dataset_id in dataset_ids
            # )
            value_headers = ("Interpolation value",)
        else:
            value_headers = tuple(
                future_change_factor_label(config, dataset_id, nice=False)
                for dataset_id in dataset_ids
            )

        writer.writerow(
            tuple(
                config["ui"]["labels"]["download_table"][k]
                for k in ("dv", "units")
            )
            + value_headers
        )
        for design_variable, data_row in zip(design_variables, data_values):
            writer.writerow(
                (
                    design_variable,
                    dv_units(
                        config, design_variable, climate_regime, nice=False
                    ),
                )
                + tuple(
                    round_to_multiple(
                        data_value,
                        dv_roundto(config, design_variable, climate_regime),
                    )
                    for dataset_id, data_value in zip(dataset_ids, data_row)
                )
            )
