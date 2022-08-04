import os.path
from pkg_resources import resource_filename
import logging
from dve.dict_utils import path_get


logger = logging.getLogger(__name__)


def file_exists(filepath):
    filepath = resource_filename("dve", filepath)
    return os.path.isfile(filepath)


def validate_filepath(filepath):
    if not file_exists(filepath):
        logger.warning(f"'{filepath}' does not exist or is not a file")


def validate_config(config, cfg_path, log=logger.warning, **kwargs):
    """
    Validate the config addressed by `cfg_path`. If there is nothing at the
    specified path in the config object, log this fact. Otherwise, validate
    the filepath found at that path.
    """
    filepath = path_get(config, cfg_path, **kwargs)
    if filepath is None:
        log(f"Expected config at '{cfg_path}' is not present.")
    else:
        validate_filepath(filepath)


def validate(config):
    """
    Validate a configuration. Specifically:
    - Check that all filepaths specified in config exist. Log a warning message
      for those which do not exist.
    """
    for filepath in config["values"]["paths"].values():
        validate_filepath(filepath)

    for design_variable in config["values"]["ui"]["dvs"]:

        # Validate historical filepaths, if present
        cfg_base_path = f"dvs/{design_variable}/historical/datasets"
        if path_get(config, cfg_base_path, separator="/") is None:
            logger.info(
                f"No historical datasets specified for {design_variable}"
            )
        else:
            for cfg_ext_path in (
                "model",
                "reconstruction",
                "stations/path",
                "table_C2",
            ):
                validate_config(
                    config, f"{cfg_base_path}/{cfg_ext_path}", separator="/"
                )

        # Validate future filepaths, if present.
        cfg_base_path = f"dvs/{design_variable}/future/datasets"
        if path_get(config, cfg_base_path, separator="/") is None:
            logger.info(f"No future datasets specified for {design_variable}")
        else:
            for cfg_ext_path in config["values"]["ui"]["future_change_factors"]:
                validate_config(
                    config, f"{cfg_base_path}/{cfg_ext_path}", separator="/"
                )
