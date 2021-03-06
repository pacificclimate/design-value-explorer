def download_filename(lon, lat):
    """
    Return a unique filename the download data for position lon, lat.

    :param lon:
    :param lat:
    :return: string
    """
    return f"dvs_{lon}_{lat}.csv"


def download_filepath(lon, lat, directory="/downloads/by-location"):
    """
    Return a unique filepath for the download data for position lon, lat.
    :param lon:
    :param lat:
    :return: string
    """
    return f"{directory}/{download_filename(lon, lat)}"
