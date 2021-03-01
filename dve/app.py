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


    def dv_nv(name, dataset, ix, iy):
        dv_ = data[name]["dv"]
        return (
            f"{name} ({dv_})",
            data[name][dataset][dv_].values[iy, ix]
        )

    @app.callback(
        Output("hover-info", "children"),
        [
            Input("my-graph", "hoverData"),
            Input("design-value-id-ctrl", "value"),
            Input("dataset-ctrl", "value"),
        ]
    )
    def display_hover_info(hover_data, design_value_id_ctrl, dataset_ctrl):
        # TODO: Can we use a fixed value ("model" or "reconstruction" instead
        #  of dataset_ctrl?

        if hover_data is None:
            lat, lon, z, source = ("--",) * 4
            items = tuple()
        else:
            curve_number, x, y = (
                hover_data["points"][0][name]
                for name in ("curveNumber", "x", "y")
            )
            ds = data[design_value_id_ctrl][dataset_ctrl]
            ix = find_nearest_index(ds.rlon.values, x)
            iy = find_nearest_index(ds.rlat.values, y)
            lat = ds.lat.values[iy, ix]
            lon = ds.lon.values[iy, ix] - 360

            try:
                z = hover_data["points"][0][{4: "z", 5: "text"}[curve_number]]
            except KeyError:
                z = f"Unknown curveNumber {curve_number}"

            try:
                source = {4: "Interp", 5: "Station"}[curve_number]
            except KeyError:
                source = f"?"

            dv_items = tuple(
                dv_nv(name, dataset_ctrl, ix, iy) for name in config["dvs"].keys()
            )

            items = (
                ("Lat", lat),
                ("Lon", lon),
                (f"Z ({design_value_id_ctrl} )({source})", z),
            ) + dv_items

        return dbc.Table(
            [
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Th(name, style={"width": "5em"}),
                                html.Td(
                                    round(value, 6) if isinstance(value, float)
                                    else value
                                )
                            ]
                        )
                        for name, value in items
                    ]
                )
            ],
            bordered=True,
            size="sm",
        )


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
    def display_click_info(click_data, design_value_id_ctrl, dataset_ctrl):
        # TODO: Can we use a fixed value ("model" or "reconstruction" instead
        #  of dataset_ctrl? ... The grids for each are slightly different and
        #  give slightly different values for lat/lon at the same pointer locn.
        # TODO: DRY
        if click_data is None:
            lat, lon, z = ("--",) * 3
            dv_items = tuple()
            nearbys = html.P("nearbys")
        else:
            curve_number, x, y = (
                click_data["points"][0][name]
                for name in ("curveNumber", "x", "y")
            )
            ds = data[design_value_id_ctrl][dataset_ctrl]
            ix = find_nearest_index(ds.rlon.values, x)
            iy = find_nearest_index(ds.rlat.values, y)
            lat = ds.lat.values[iy, ix]
            lon = ds.lon.values[iy, ix] - 360

            try:
                z = click_data["points"][0][{4: "z", 5: "text"}[curve_number]]
            except KeyError:
                z = f"Unknown curveNumber {curve_number}"

            dv_items = tuple(
                dv_nv(name, dataset_ctrl, ix, iy) for name in config["dvs"].keys()
            )

            nearbys = dbc.Table(
                [
                    html.Tbody(
                        [html.Tr(html.Th(name, colSpan=3))] +
                        [
                            html.Tr(
                                [
                                    html.Td(dv_nv(name, dataset_ctrl, ix + di, iy + dj)[1])
                                    for di in (-1, 0, 1)
                                ]
                            )
                            for dj in (1, 0, -1)
                        ]
                    )
                    for name in config["dvs"].keys()
                ]
            )

        items = (
            ("Lat", lat),
            ("Lon", lon),
            ("Z", z),
        ) + dv_items

        return [
            dbc.Table(
                [
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Th(name, style={"width": "5em"}),
                                    html.Td(
                                        round(value, 6) if isinstance(value, float)
                                        else value
                                    )
                                ]
                            )
                            for name, value in items
                        ],
                    ),
                ],
                bordered=True,
                size="sm",
            ),
            # nearbys,
            # dbc.Table(
            #     [
            #         html.Thead(
            #           [
            #               html.Tr(
            #                   [html.Th("DV name"), html.Th("")]
            #               )
            #           ],
            #         ),
            #         html.Tbody(
            #             [
            #                 html.Tr(
            #                     [
            #                         html.Th(name, style={"width": "5em"}),
            #                         html.Td(
            #                             round(value, 6) if isinstance(value, float)
            #                             else value
            #                         )
            #                     ]
            #                 )
            #                 for name, value in zip(("Lat", "Lon"), (lat, lon))
            #             ]
            #         ),
            #
            #     ],
            #     bordered=True,
            #     size="sm",
            # ),
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

    return app
