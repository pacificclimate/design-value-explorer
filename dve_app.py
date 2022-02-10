from argparse import ArgumentParser
import logging.config
import yaml
from dve.app import make_app


# Set up logging. Logging config is not in main app configuration.
logging_config_filepath="logging.yml"
with open(logging_config_filepath, "r") as logging_config_file:
    logging_config = yaml.safe_load(logging_config_file)
logging.config.dictConfig(logging_config)
logger = logging.getLogger("dve")


# Create app
app = make_app()
# Expose Flask server for deployment with Gunicorn
server = app.server


if __name__ == "__main__":
    # Set up logging
    log_level_choices = "NOTSET DEBUG INFO WARNING ERROR CRITICAL".split()

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
    # TODO: Possibly remove; logging config is now in `logging.yml`.
    parser.add_argument(
        "-l",
        "--loglevel",
        help="Logging level",
        choices=log_level_choices,
        default=None,
    )
    args = parser.parse_args()
    loglevel = args.loglevel or ("DEBUG" if args.debug else "INFO")
    logger.setLevel(getattr(logging, loglevel))

    logger.debug("Running app on development server")
    app.run_server(
        host='0.0.0.0',
        port=5000,
        debug=args.debug,
    )
