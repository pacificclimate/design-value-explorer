import json

from climpyrical.data import read_data
from climpyrical.gridding import flatten_coords, transform_coords, find_nearest_index
from climpyrical.mask import stratify_coords
from climpyrical.cmd.find_matched_model_vals import add_model_values
from dve.colorbar import get_cmap_divisions, matplotlib_to_plotly, plotly_discrete_colorscale

import dve
import dve.data
import dve.layout
from dve.processing import coord_prep
from dve.generate_iso_lines import gen_lines

import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import numpy as np
import matplotlib.cm
import geopandas as gpd
from pkg_resources import resource_filename

from dve.utils import sigfigs

import flask
import os
import warnings
import logging
import uuid
import csv


def get_app(config, data):
    warnings.filterwarnings("ignore")

    # load polygon data
    canada = gpd.read_file(
        resource_filename("dve", config["paths"]["canada_vector"])
    ).geometry
    X, Y = stratify_coords(canada)

    native_mask = read_data(
        resource_filename("dve", config["paths"]["native_mask"])
    )["sftlf"] >= 1.0

    # initialize app
    TIMEOUT = 60
    server = flask.Flask("app")
    app = dash.Dash("app", server=server)
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = 'Pacific Climate Impacts Consortium Design Value Explorer'
    app.config.suppress_callback_exceptions = True

    app.layout = dve.layout.main(config, data)


    @app.callback(
        Output("table", "children"),
        [Input("design-value-id-ctrl", "value")]
    )
    def update_tablec2(value):
        df = data[value]["table"]
        df = df[["Location", "lon", "lat", data[value]["station_dv"]]].round(3)

        return dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={
                        'textAlign': 'center',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'padding': '5px'
                    },
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': 'white',
                        'fontWeight': 'bold'
                    },
                    data=df.to_dict('records'),
               )


    # TODO: Element "input-colorbar-output-container" does not exist (any more?)
    #   in the layout. Therefore this callback has no effect or purpose. Remove?
    @app.callback(
        Output("input-colorbar-output-container", "children"),
        [Input("input-colorbar", "value")]
    )
    def update_input(value):
        try:
            matplotlib.cm.get_cmap(value, 10)
        except ValueError:
            value = "Invalid cmap!"
        return f"Colour Map: {value}"


    @app.callback(
        Output("range-slider-output-container", "children"),
        [Input("range-slider", "value")]
    )
    def update_range(value):
        return f"Range: {sigfigs(value[0])} to {sigfigs(value[1])}"

    @app.callback(
        [
            Output(component_id="range-slider", component_property="min"),
            Output(component_id="range-slider", component_property="max"),
            Output(component_id="range-slider", component_property="step"),
            Output(component_id="range-slider", component_property="value")
        ],
        [Input(component_id="design-value-id-ctrl", component_property="value"),
        Input(component_id="cbar-slider", component_property="value")],
    )
    def update_slider(value, N):
        field = data[value]["reconstruction"][data[value]["dv"]].values
        minimum = np.round(np.nanmin(field), 3)
        maximum = np.round(np.nanmax(field), 3)
        step = (maximum-minimum)/(N+1)
        default = [minimum, maximum]
        return minimum, maximum, step, default


    # TODO: Remove when no longer needed for development
    # @app.callback(
    #     Output("hover-data", "children"),
    #     [Input("my-graph", "hoverData")]
    # )
    # def display_hover_data(hover_data):
    #     return json.dumps(hover_data, indent=2)


    # TODO: Remove?
    def dv_nv(name, interpolation, ix, iy):
        data_var_name = data[name]["dv"]
        return (
            f"{name} ({data_var_name})",
            data[name][interpolation][data_var_name].values[iy, ix]
        )


    def pointer_rlonlat(pointer_data):
        if pointer_data is None:
            return None, None
        return tuple(pointer_data["points"][0][name] for name in ("x", "y"))



    def rlonlat_to_indices(dataset, rlon, rlat):
        ix = find_nearest_index(dataset.rlon.values, rlon)
        iy = find_nearest_index(dataset.rlat.values, rlat)
        return ix, iy


    def pointer_indices(pointer_data, dataset):
        if pointer_data is None:
            return None, None
        # TODO: DRY
        rlon, rlat = (pointer_data["points"][0][name] for name in ("x", "y"))
        ix = find_nearest_index(dataset.rlon.values, rlon)
        iy = find_nearest_index(dataset.rlat.values, rlat)
        return ix, iy


    def pointer_lonlat(ds, ix, iy):
        if ix is None or iy is None:
            return None, None
        lat = ds.lat.values[iy, ix]
        lon = ds.lon.values[iy, ix] - 360
        return lon, lat


    def pointer_value(pointer_data):
        curve_number = pointer_data["points"][0]["curveNumber"]

        try:
            z = pointer_data["points"][0][{4: "z", 5: "text"}[curve_number]]
        except KeyError:
            z = None

        try:
            source = {4: "Interp", 5: "Station"}[curve_number]
        except KeyError:
            source = None

        return z, source


    def value_table(*items):
        return dbc.Table(
            [
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Th(name, style={"width": "5em"}),
                                html.Td(value),
                            ]
                        )
                        for name, value in items
                    ]
                )
            ],
            bordered=True,
            size="sm",
        )


    def dv_value(name, interpolation, rlon, rlat):
        var_name = data[name]["dv"]
        dataset = data[name][interpolation]
        ix, iy = rlonlat_to_indices(dataset, rlon, rlat)
        # print(f"ix={ix}, iy={iy}, var_name={var_name},")
        # print(f"data[name] {data[name]}")
        return dataset[var_name].values[iy, ix]


    def dv_table(rlon, rlat, selected_dv=None, selected_interp=None):
        """
        Return a table listing values of design values at a location specified
        by rotated coordinates rlon, rlat

        :param rlon:
        :param rlat:
        :return:
        """
        return dbc.Table(
            [
                html.Thead(
                    [
                        html.Tr(
                            [
                                html.Th("DV"),
                                html.Th("Model"),
                                html.Th("Reconstruction"),
                            ]
                        )
                    ]
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [html.Th(name, style={"width": "5em"})] +
                            [
                                html.Td(
                                    round(float(dv_value(name, interp, rlon, rlat)), 3),
                                    style={"color": "red" if name == selected_dv and interp == selected_interp else "inherit"}
                                )
                                for interp in ("model", "reconstruction")
                            ]
                        )
                        for name in config["dvs"].keys()
                    ],
                )
            ],
            bordered=True,
            size="sm",
        )


    @app.callback(
        Output("hover-info", "children"),
        [
            Input("my-graph", "hoverData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ]
    )
    def display_hover_info(
        hover_data, design_value_id_ctrl, interpolation_ctrl
    ):
        # TODO: Can we use a fixed value ("model" or "reconstruction") instead
        #  of interpolation_ctrl? Note: Each type of dataset has a different
        #  lat-lon grid.

        if hover_data is None:
            return "no hover"

        dataset = data[design_value_id_ctrl][interpolation_ctrl]
        rlon, rlat = pointer_rlonlat(hover_data)
        ix, iy = pointer_indices(hover_data, dataset)
        lon, lat = pointer_lonlat(dataset, ix, iy)
        z, source = pointer_value(hover_data)

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
                # ("ix", ix),
                # ("iy", iy),
            ),
            dv_table(
                rlon,
                rlat,
                selected_dv=design_value_id_ctrl,
                selected_interp=interpolation_ctrl
            ),
        ]



    # TODO: Remove when no longer needed for development
    # @app.callback(
    #     Output("click-data", "children"),
    #     [Input("my-graph", "clickData")]
    # )
    # def display_click_data(click_data):
    #     return json.dumps(click_data, indent=2)


    @app.callback(
        Output("click-info", "children"),
        [
            Input("my-graph", "clickData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ]
    )
    def display_click_info(
        click_data, design_value_id_ctrl, interpolation_ctrl
    ):
        # TODO: Can we use a fixed value ("model" or "reconstruction" instead
        #  of interp_ctrl? ... The grids for each are different and
        #  give different values for lat/lon at the same pointer locn.
        # TODO: DRY
        if click_data is None:
            return "no click"

        dataset = data[design_value_id_ctrl][interpolation_ctrl]
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_indices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = pointer_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        # Create data table for download
        download_filepath = f"/downloads/by-location/{uuid.uuid1()}.csv"
        with open(download_filepath, "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(("Latitude", lat))
            writer.writerow(("Longitude", lon))
            writer.writerow(tuple())
            writer.writerow(
                ("Design Value ID", "Model Value", "Reconstruction Value")
            )
            for dv_id in config["dvs"].keys():
                writer.writerow(
                    (
                        dv_id,
                        float(dv_value(dv_id, "model", rlon, rlat)),
                        float(dv_value(dv_id, "reconstruction", rlon, rlat)),
                    )
                )

        return [
            html.A(
                "Download this data",
                href=download_filepath,
                download=f"dvs_{lon}_{lat}.csv",
                className="btn btn-primary btn-sm mb-1"
            ),
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
                # *(
                #     dv_nv(name, dataset_ctrl, ix, iy)
                #     for name in config["dvs"].keys()
                # )
            ),
            dv_table(
                rlon,
                rlat,
                selected_dv=design_value_id_ctrl,
                selected_interp=interpolation_ctrl
            ),
        ]


    # TODO: What is this?
    ds = data[list(data.keys())[0]]["reconstruction"]

    @app.callback(
        Output("my-graph", "figure"),
        [
            Input("mask-ctrl", "on"),
            Input("stations-ctrl", "on"),
            Input("design-value-id-ctrl", "value"),
            Input("cbar-slider", "value"),
            Input("range-slider", "value"),
            Input("dataset-ctrl", "value"),
            Input("scale-ctrl", "value"),
            Input("colour-map-ctrl", "value"),
            Input("raster-ctrl", "on"),
        ],
    )
    def update_ds(
        mask_ctrl,
        stations_ctrl,
        design_value_id_ctrl,
        cbar_slider,
        range_slider,
        dataset_ctrl,
        scale_ctrl,
        colour_map_ctrl,
        raster_ctrl
    ):

        zmin = range_slider[0]
        zmax = range_slider[1]

        if scale_ctrl == "logarithmic":
            ticks = np.linspace(np.log10(zmin), np.log10(zmax), cbar_slider + 1)
            ticks = np.around(10**(ticks), 2)
        else:
            ticks = np.around(np.linspace(zmin, zmax, cbar_slider + 1), 3)

        if colour_map_ctrl is None:
            colour_map_ctrl = data[design_value_id_ctrl]["cmap"]

        cmap = matplotlib.cm.get_cmap(colour_map_ctrl, cbar_slider)

        colours = [
            matplotlib.colors.rgb2hex(cmap(i))
            for i in range(cmap.N)
        ]

        discrete_colorscale = plotly_discrete_colorscale(ticks, colours)

        r_or_m = dataset_ctrl

        dv = data[design_value_id_ctrl]["dv"]
        station_dv = data[design_value_id_ctrl]["station_dv"]
        ds = data[design_value_id_ctrl][r_or_m]
        df = data[design_value_id_ctrl]["stations"]

        x1 = min(value for value in X if value is not None)
        x2 = max(value for value in X if value is not None)
        y1 = min(value for value in Y if value is not None)
        y2 = max(value for value in Y if value is not None)


        ixmin = find_nearest_index(ds.rlon.values, np.nanmin(x1))
        ixmax = find_nearest_index(ds.rlon.values, np.nanmax(x2))
        iymin = find_nearest_index(ds.rlat.values, np.nanmin(y1))
        iymax = find_nearest_index(ds.rlat.values, np.nanmax(y2))

        go_list = gen_lines(ds, X, Y)

        # need to process stations
        df = coord_prep(df, station_dv)
        ds_arr = ds[dv].values[iymin:iymax, ixmin:ixmax].copy()

        if r_or_m == "model" and mask_ctrl:
            mask = native_mask[iymin:iymax, ixmin:ixmax]
            ds_arr[~mask] = np.nan

        fig_list = [
                go.Heatmap(
                    z=ds_arr,
                    x=ds.rlon.values[ixmin:ixmax],
                    y=ds.rlat.values[iymin:iymax],
                    zmin=zmin,
                    zmax=zmax,
                    hoverongaps=False,
                    colorscale = discrete_colorscale,
                    colorbar={"tickvals": ticks},
                    visible=raster_ctrl,
                    hovertemplate=(
                        f"<b>{design_value_id_ctrl} (Interp.): %{{z}} </b><br>"
                    ),
                    name=""
                ),
                go.Scattergl(
                    x=df.rlon,
                    y=df.rlat,
                    text=df[station_dv],
                    mode="markers",
                    marker=dict(
                        size=10,
                        symbol="circle",
                        color=df[station_dv],
                        cmin=zmin,
                        cmax=zmax,
                        line=dict(
                            width=1,
                            color="DarkSlateGrey"
                        ),
                        showscale=(raster_ctrl == False),
                        colorscale = discrete_colorscale,
                        colorbar={"tickvals": ticks},
                    ),
                    hovertemplate=(
                        f"<b>{design_value_id_ctrl} (Station): "
                        f"%{{text}}</b><br>"
                    ),
                    visible=stations_ctrl,
                    name=""
                ),
            ]

        go_list += fig_list
        units = ds[dv].attrs["units"]
        fig = {
            "data": go_list,
            "layout": {
                "title": (
                    f"<b>{design_value_id_ctrl} "
                    f"[{config['dvs'][design_value_id_ctrl]['description']}] "
                    f"({units})</b>"
                ),
                "font": dict(size=13, color='grey'),
                "xaxis": dict(
                    zeroline=False,
                    range=[ds.rlon.values[ixmin], ds.rlon.values[ixmax]],
                    showgrid=False, # thin lines in the background
                    visible=False  # numbers below
                ),
                "yaxis": dict(
                    zeroline=False,
                    range=[ds.rlat.values[iymin], ds.rlat.values[iymax]],
                    showgrid=False, # thin lines in the background
                    visible=False
                ),
                'xaxis_showgrid': False,
                'yaxis_showgrid': False,
                "hoverlabel": dict(
                    bgcolor="white",
                    font_size=16,
                    font_family="Rockwell"
                ),
                "hoverdistance": 5,
                "hovermode": "closest",
                "width": 1000,
                "height": 750,
                "showlegend": False,
                "legend_orientation": "v",
                "scrollZoom": True,
                "uirevision": "None"
            }
        }

        return fig


    @app.server.route("/downloads/by-location/<filename>")
    def serve_static(filename):
        return flask.send_from_directory(
            os.path.join('/downloads/by-location'), filename
        )

    return app
