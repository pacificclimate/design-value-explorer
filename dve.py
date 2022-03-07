from argparse import ArgumentParser
import logging.config
import yaml
from dve.app import make_app


if __name__ == "__main__":
    # Set up development HTTP server logging. This affects only the logging
    # done by this server, not by the app, and not by the production server,
    # which is run using Gunicorn which has its own logging configuration.
    # See notes above re. logging.
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
    app = make_app()
    app.run_server(
        host='0.0.0.0',
        port=5000,
        debug=args.debug,
    )
