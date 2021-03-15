import os


dash_url_base_path = os.environ.get("DASH_URL_BASE_PATHNAME", "/")
download_by_location_dir = "downloads/by-location"


def download_filename(lon, lat):
    """
    Return a unique filename the download data for position lon, lat.

    :param lon:
    :param lat:
    :return: string
    """
    return f"dvs_{lon}_{lat}.csv"


def download_filepath(lon, lat, directory=download_by_location_dir):
    """
    Return a unique filepath for the download data for position lon, lat.
    :param lon:
    :param lat:
    :param directory: File directory containing files for downloading.
    :return: string
    """
    return os.path.join(directory, download_filename(lon, lat))


def download_base_url(
    base_path=dash_url_base_path,
    directory=download_by_location_dir,
):
    return os.path.join(base_path, directory)


def download_url(
    lon, lat, base_path=dash_url_base_path, directory=download_by_location_dir
):
    return os.path.join(base_path, download_filepath(lon, lat, directory))
