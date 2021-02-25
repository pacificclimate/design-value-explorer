# Design Value Explorer

Plotly/Dash for interactive visualization of design value fields.

## Build Status

![Docker Publishing](https://github.com/pacificclimate/dash-dv-explorer/workflows/Docker%20Publishing/badge.svg)

## Cloning the project

Clone this repository
```
git clone https://github.com/pacificclimate/dash-dv-explorer/
```

Because we primarily use a Docker image to run the code for testing and
development, there is (normally) no need to install and run the project 
directly on a development machine.

## App configuration

Configuration paths go into `config.yml`. An example is provided by default. Note that the paths are not absolute, and use `resource_pkgs.resource_filename` set within `dve/` as a reference.

The generic recipe is:
```yaml
paths:
    mask_path: data/masks/canada_mask_rp.nc
    north_mask_path: data/masks/canada_mask_north_rp.nc
    canada_vector: data/vectors/canada_final.shp
    native_mask: data/masks/land_mask_CanRCM4_sftlf.nc
    total_table_c2: data/tables/combined_dv_tablec2.csv
dvs:
    RL50: # appears in dropdown
        station_dv: "RL50 (kPa)" # As found in the station DV column csv
        station_path: data/station_inputs/sl50_rl50_for_maps.csv # station csv (requires lat, lon columns)
        input_model_path: data/model_inputs/snw_rain_CanRCM4-LE_ens35_1951-2016_max_rl50_load_ensmean.nc # is the input model path associated with the dv
        reconstruction_path: data/reconstructions/RL50_reconstruction.nc # the HSM reconstruction from climpyrical
        table: data/tables/RL50_TableC2.csv # the table generated from the HSM for NBCC locations
        cmap: "terrain_r" # default colormap
    HDD:
        station_dv: "HDD (degC-day)"
        station_path: data/station_inputs/hdd_Tmax_Tmin_allstations_v3_for_maps.csv
        input_model_path: data/model_inputs/hdd_CanRCM4-LE_ens35_1951-2016_ann_ensmean.nc
        reconstruction_path: data/reconstructions/HDD_reconstruction.nc
        table: data/tables/HDD_TableC2.csv
        cmap: "RdBu"
    # and so on...
colormaps:
    ['viridis', 'plasma', 'inferno', ...] # list of colormaps as found in matplotlib.cm
```

## Development and debugging

### Using the `dve-dev-local` Docker image

The `dve-dev-local` Docker image is the primary means for running the app while
developing and debugging. Using it has two advantages:
- It is very similar to the production environment.
- It reduces effort needed to install the supporting software.
- It maps a development configuration file onto the `config.yml`.
  Typically, this configuration has a reduced dataset to speed startup, and
  uses local copies of large files ditto.

#### Overview

This image enables the developer to run the app in a Docker container, but
with "live" code updates visible inside the container. All infrastructure for
building and running this image is in `docker/dev-local`.

The image is normally built locally. (Because of this, there is no automated
build for the dev-local image as there is for the production image.) The image
installs the dependencies listed in `requirements.txt`, but does not install
`dash-dev-explorer`. The image need only be rebuilt when project dependencies 
(`requirements.txt`) change.

After building, the image is run locally, and the
local codebase for `dash-dv-explorer` is mounted to it.
The container's first step (via the ENTRYPOINT) is to install that 
local codebase. 
With this arrangement, changes to the local codebase are available
directly inside the container. The container does not need to be restarted,
nor does the image need to be rebuilt in order to test code changes.

With the container running, the developer can run commands from inside it by
using `docker exec` commands. Most convenient is to use `docker exec` to run
an interactive `bash` shell in the container. From that bash shell all ordinary
commands can be run, including running tests and running the app.

#### Prepare

1. Update the development config (`docker/dev-local/config.yml`) as needed.
1. Copy any large datasets (e.g., reconstructions) to your local codebase
   (typically under `local-data/`). This cuts app startup time from minutes
   to seconds. App startup is incurred every time you make a change to the
   codebase and want to see the results.

#### Build the image

The image need only be (re)built when the project is first cloned and when 
`requirements.txt` changes. To build the image:

```
docker-compose -f docker/dev-local/docker-compose.yml build
```

The image name is `pcic/dve-dev-local`.

#### Start the container

```
docker-compose -f docker/dev-local/docker-compose.yml up -d
```

The container name is `dve-dev-local`.

#### Connect to a bash shell inside the container

When the container is running, you can connect to it and run a bash shell
inside it with

```
docker exec -it dve-dev-local bash
```

You will see a prompt like

```
root@f4bcdc72b9f2:/codebase# 
```

At this prompt you can enter bash commands, including the following:

#### Start the app inside the container

From the bash prompt:

```
python run_app.py
```

Aside: Dash apps are based on Flask. 
Flask documentation 
[stronly recommends](https://flask.palletsprojects.com/en/1.1.x/server/#command-line)
running apps for development using the Flask command line `flask run`.
Unfortunately, that does not work for a Dash app, and we must run it more
directly from a script as above. 

This enables the development environment, including the interactive debugger 
and reloader, and then starts the server on `http://localhost:5000/`.

For more details, see the link above.


#### Stop the container

When you have completed a cycle of development and testing, you may wish
to stop the Docker container.

```
docker-compose -f docker/dev-local/docker-compose.yml down
```

## Installing and running directly (no Docker)

Installing and running directly in the local environment is not recommended,
mainly because it requires data files to be copied (or linked) into the project 
directories. This is better accomplished by mounting them to a Docker image
that runs the app.

If for some reason, you do need to install and run the app directly, here's how.

### Install requirements
```
pip install -r dash-dv-explorer/requirements.txt
```

This installation may fail if Cython is not explicitly installed first.

### Install DVE
```
pip install -e dash-dv-explorer
```

### Run

If you have *all* datafiles copied into the local project
(i.e., the necessary datafiles in all `dve/data/` sudirectories), then you
can launch the app locally with.

```
export FLASK_APP=run_app.py
export FLASK_ENV=development
flask run
```

This enables the development environment, including the interactive debugger 
and reloader, and then starts the server on `http://localhost:5000/`.

## Deploying to production

A production Docker image is automatically built. In a while I will tell you
how to deploy it.

**TBD**

## Authors

- Nic Annau, nannau@uvic.ca, Pacific Climate Impacts Consortium
- Rod Glover, rglover@uvic.ca, Pacific Climate Impacts Consortium
