from climpyrical.data import read_data
from climpyrical.gridding import flatten_coords, transform_coords, find_nearest_index
from climpyrical.mask import stratify_coords
from climpyrical.cmd.find_matched_model_vals import add_model_values
from dve.colorbar import get_cmap_divisions, matplotlib_to_plotly, discrete_colorscale

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

    colormaps = config["colormaps"]
    # Add reverse options, too
    cmap_r = tuple(f"{color}_r" for color in colormaps)
    colormaps += cmap_r

    # initialize app
    TIMEOUT = 60
    server = flask.Flask("app")
    app = dash.Dash("app", server=server)
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = 'Pacific Climate Impacts Consortium Design Value Explorer'
    app.config.suppress_callback_exceptions = True

    app.layout = dve.layout.main(data, colormaps)

    @app.callback(
        dash.dependencies.Output("ens-output-container", "children"),
        [dash.dependencies.Input("ens-switch", "value")]
    )
    def update_ensemble(value):
        d = {True: "CanRCM4 Ensemble Mean", False: "HSM Reconstruction"}
        return f"{d[value]}"

    @app.callback(
        dash.dependencies.Output("raster-output-container", "children"),
        [dash.dependencies.Input("raster-switch", "value")]
    )
    def update_ensemble(value):
        d = {True: "Raster On", False: "Raster Off"}
        return f"{d[value]}"


    @app.callback(
        dash.dependencies.Output("table", "children"),
        [dash.dependencies.Input("design-value-name", "value")]
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


    @app.callback(
        dash.dependencies.Output("mask-output-container", "children"),
        [dash.dependencies.Input("toggle-mask", "value")]
    )
    def update_mask(value):
        d = {True: "ON", False: "OFF"}
        return f"Mask: {d[value]}"

    @app.callback(
        dash.dependencies.Output("log-output-container", "children"),
        [dash.dependencies.Input("toggle-log", "value")]
    )
    def update_log(loglin):
        d = {True: "Log", False: "Linear"}
        return f"Colourscale: {d[loglin]}"


    # TODO: Element "input-colorbar-output-container" does not exist (any more?)
    #   in the layout. Therefore this callback has no effect or purpose. Remove?
    @app.callback(
        dash.dependencies.Output("input-colorbar-output-container", "children"),
        [dash.dependencies.Input("input-colorbar", "value")]
    )
    def update_input(value):
        try:
            matplotlib.cm.get_cmap(value, 10)
        except ValueError:
            value = "Invalid cmap!"
        return f"Colour Map: {value}"

    @app.callback(
        dash.dependencies.Output("station-output-container", "children"),
        [dash.dependencies.Input("toggle-station-switch", "value")],
    )
    def update_stations(value):
        d = {True: "ON", False: "OFF"}
        return f"Stations: {d[value]}"


    @app.callback(
        dash.dependencies.Output("range-slider-output-container", "children"),
        [dash.dependencies.Input("range-slider", "value")]
    )
    def update_range(value):
        return f"Colourbar Range: {value[0]} to {value[1]}"

    @app.callback(
        [
            Output(component_id="range-slider", component_property="min"),
            Output(component_id="range-slider", component_property="max"),
            Output(component_id="range-slider", component_property="step"),
            Output(component_id="range-slider", component_property="value")
        ],
        [Input(component_id="design-value-name", component_property="value"),
        Input(component_id="cbar-slider", component_property="value")],
    )
    def update_slider(value, N):
        field = data[value]["reconstruction"][data[value]["dv"]].values
        minimum = np.round(np.nanmin(field), 3)
        maximum = np.round(np.nanmax(field), 3)
        step = (maximum-minimum)/(N+1)
        default = [minimum, maximum]
        return minimum, maximum, step, default


    @app.callback(
        dash.dependencies.Output("cbar-slider-output-container", "children"),
        [dash.dependencies.Input("cbar-slider", "value")],
    )
    def update_slider_n(value):
        return f"Number of Discrete Colours = {value}"

    ds = data[list(data.keys())[0]]["reconstruction"]

    @app.callback(
        dash.dependencies.Output("my-graph", "figure"),
        [
            dash.dependencies.Input("toggle-mask", "value"),
            dash.dependencies.Input("toggle-station-switch", "value"),
            dash.dependencies.Input("design-value-name", "value"),
            dash.dependencies.Input("cbar-slider", "value"),
            dash.dependencies.Input("range-slider", "value"),
            dash.dependencies.Input("ens-switch", "value"),
            dash.dependencies.Input("toggle-log", "value"),
            dash.dependencies.Input("colorscale", "value"),
            dash.dependencies.Input("raster-switch", "value"),
        ],
    )
    def update_ds(
        toggle_mask,
        toggle_station_switch,
        design_value_name,
        cbar_slider,
        range_slider,
        mean_button,
        toggle_log,
        colorscale,
        raster_switch
    ):

        zmin = range_slider[0]
        zmax = range_slider[1]

        if toggle_log:
            ticks = np.linspace(np.log10(zmin), np.log10(zmax), cbar_slider + 1)
            ticks = np.around(10**(ticks), 2)
        else:
            ticks = np.around(np.linspace(zmin, zmax, cbar_slider + 1), 3)

        if colorscale is None:
            colorscale = data[design_value_name]["cmap"]

        cmap = matplotlib.cm.get_cmap(colorscale, cbar_slider)

        hexes = []
        for i in range(cmap.N):
            rgba = cmap(i)
            # rgb2hex accepts rgb or rgba
            hexes.append(matplotlib.colors.rgb2hex(rgba))

        dcolorsc = discrete_colorscale(ticks, hexes)
        ticktext = [f'{ticks[0]}-{ticks[1]}'] + [f'{ticks[k]}-{ticks[k+1]}' for k in range(1, len(ticks)-1)]

        r_or_m = "model" if mean_button else "reconstruction"

        dv, station_dv = data[design_value_name]["dv"], data[design_value_name]["station_dv"]
        ds = data[design_value_name][r_or_m]
        df = data[design_value_name]["stations"]

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

        if r_or_m == "model" and toggle_mask:
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
                    colorscale = dcolorsc,
                    colorbar = dict(
                        tickvals=ticks,
                        ticktext=ticktext
                    ),
                    visible=raster_switch,
                    hovertemplate="<b>Design Value: %{z} </b><br>",
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
                        showscale=(raster_switch==False),
                        colorscale = dcolorsc,
                        colorbar = dict(
                            tickvals=ticks,
                            ticktext=ticktext,
                        ),
                    ),
                    hovertemplate="<b>Station Value: %{text}</b><br>",
                    visible=toggle_station_switch,
                    name=""
                ),
            ]

        go_list += fig_list
        units = ds[dv].attrs["units"]
        fig = {
            "data": go_list,
            "layout": {
                "title": f"<b>{design_value_name} ({units})</b>",
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
