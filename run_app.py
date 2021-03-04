from argparse import ArgumentParser
import logging
import yaml
from dve.data import load_data
from dve.app import get_app


# Set up logging
logger = logging.getLogger("dve")
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
log_level_choices = "NOTSET DEBUG INFO WARNING ERROR CRITICAL".split()


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Run the Design Value Explorer Dash app"
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=False,
        action="store_true",
        help="Run in debug mode",
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        help="Logging level",
        choices=log_level_choices,
        default="INFO",
    )
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    logger.debug("Loading configuration")
    with open("config.yml", "r") as ymlfile:
        config = yaml.load(ymlfile)
    logger.debug(f"Configuration loaded. {config}")

    data = load_data(config)

    app = get_app(config, data)

    logger.debug("### Running app")
    app.run_server(
        host='0.0.0.0',
        port=5000,
        debug=args.debug,
    )
