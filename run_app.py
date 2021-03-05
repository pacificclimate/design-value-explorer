from argparse import ArgumentParser
import logging
from dve.app import make_app


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
        default=None,
    )
    args = parser.parse_args()
    loglevel = args.loglevel or ("DEBUG" if args.debug else "INFO")
    logger.setLevel(getattr(logging, loglevel))

    app = make_app()

    logger.debug("Running app on development server")
    app.run_server(
        host='0.0.0.0',
        port=5000,
        debug=args.debug,
    )
