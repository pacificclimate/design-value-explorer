# Configuration
- [Major deployment parameters: environment variables](#major-deployment-parameters-environment-variables)
- [App behaviour configuration: app-config](#app-behaviour-configuration-app-config)
- [App logging configuration](#app-logging-configuration)
- [Gunicorn logging configuration](#gunicorn-logging-configuration)

## Major deployment parameters: environment variables

Environment variables configure major deployment parameters such as the
base path name and Gunicorn parameters.

`DASH_URL_BASE_PATHNAME`
- Base path for the app and all associated URLs including downloads

`LARGE_FILE_CACHE_SIZE`
- Number of large files (e.g., NetCDF data files) cached inside the app.

`SMALL_FILE_CACHE_SIZE`
- Number of small files (e.g., CSV files) cached inside the app.

`GUNICORN_<param>`
- GUNICORN configuration parameters. The Gunicorn configuration file
  (`docker/production/gunicorn.conf`) scrapes all environment variables
  of the form `GUNICORN_<param>` and sets value of configuration parameter
  `<param>` (converted to lowercase) to the value of the environment var.

An up-to-date example of these environment variables is part of the project.
It is kept in file `docker/production/env.env`.
Please update this file if significant changes are made in production 
deployments. (It is part of the deployment template.)

## App behaviour configuration: app-config

On startup, the app loads a configuration file (`app-config.yml`) containing
parameters used to direct the behaviour of the app. Configuration
parameters include:
- User interface defaults, settings, and labels (key `ui`)
- Filepaths to some data files (key `paths`)
- Filepaths and information about each design value (key `dvs`)
- Configuration of local preferences storage (key `local_config`)
- A miscellany of other values

Notes:

1. Filepaths are not absolute, and use `resource_pkgs.resource_filename`
   set within `dve/` as a reference. This is not a desirable practice and
   will
   [change](https://github.com/pacificclimate/dash-dv-explorer/issues/111)
   to absolute, direct filepaths at some point.

2. See the module docstring for module `dve/callbacks/local_preferences. py`
   for details on how to configure local preferences. 

## App logging configuration

Logging by the app proper is configured in `app-config.yml`.
An up-to-date example of this file is part of the project. Please update 
this file if significant changes are made in production deployments.
(It is part of the deployment template.)

## Gunicorn logging configuration

In production deployments, Gunicorn logging is configured in
`docker/production/gunicorn-logging.conf`.
An up-to-date example of this file is part of the project. Please update
this file if significant changes are made in production deployments.
(It is part of the deployment template.)