# dash-dv-explorer
Plotly/Dash for interactive visualization of design value fields.

# Install
Clone this repository
`git clone https://github.com/pacificclimate/dash-dv-explorer/`

Install requirements
`pip install -r dash-dv-explorer/requirements.txt`

Install DVE
`pip install -e dash-dv-explorer`

# Configure
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
    RL50:
        station_dv: "RL50 (kPa)" # As found in the station DV column csv
        station_path: data/station_inputs/sl50_rl50_for_maps.csv # station csv (requires lat, lon columns)
        input_model_path: data/model_inputs/snw_rain_CanRCM4-LE_ens35_1951-2016_max_rl50_load_ensmean.nc # is the input model path associated with the dv
        reconstruction_path: data/reconstructions/RL50_reconstruction.nc # the HSM reconstruction from climpyrical
        table: data/tables/RL50_TableC2.csv # the table generated from the HSM for NBCC locations
        cmap: "terrain_r" # default colormap
colormaps:
    ['viridis', 'plasma', 'inferno', ...] # list of colormaps as found in matplotlib.cm
```

# Launching Remotely
A `Dockerfile` is provided as well as a `docker-compose.yml`. Be sure to configure for your server's settings and available ports. In `dash-dv-explorer/`

To build and run
`docker-compose build`
`docker-compose up`

# Launching locally
`python dash_app.py`
