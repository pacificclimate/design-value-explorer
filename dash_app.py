from climpyrical.data import read_data
from climpyrical.gridding import flatten_coords, transform_coords, find_nearest_index
from climpyrical.mask import stratify_coords
from climpyrical.cmd.find_matched_model_vals import add_model_values
from dve.colorbar import get_cmap_divisions, matplotlib_to_plotly, discrete_colorscale
from dve.processing import coord_prep
from dve.generate_iso_lines import gen_lines
from dve.layout import get_layout
import dve

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
import pandas as pd
import os
import warnings
import yaml
import logging


warnings.filterwarnings("ignore")

with open("config.yml", "r") as ymlfile:
    config = yaml.load(ymlfile)

# load polygon data
canada = gpd.read_file(
    resource_filename("dve", config["paths"]["canada_vector"])
).geometry
X, Y = stratify_coords(canada)

native_mask = read_data(
    resource_filename("dve", config["paths"]["native_mask"])
)["sftlf"] >= 1.0


data = {}
for key in config["dvs"].keys():
    print(config["dvs"][key]["station_path"])
    info = {"stations": pd.read_csv(
                                resource_filename(
                                    "dve",
                                    config["dvs"][key]["station_path"]
                                )
                            ),
            "model": read_data(
                            resource_filename(
                                "dve",
                                config["dvs"][key]["input_model_path"]
                            )
                        ),
            "reconstruction": read_data(
                            resource_filename(
                                "dve",
                                config["dvs"][key]["reconstruction_path"]
                            )
                        ),
            "station_dv": config["dvs"][key]["station_dv"],
            "table": pd.read_csv(
                                resource_filename(
                                    "dve",
                                    config["dvs"][key]["table"]
                                )
                            )
    }
    data[key] = info

for key in data.keys():
    (dv, ) = data[key]["model"].data_vars
    data[key]["dv"] = dv


# initialize app
TIMEOUT = 60
server = flask.Flask("app")
app = dash.Dash("app", server=server)
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Pacific Climate Impacts Consortium Design Value Explorer'
app.config.suppress_callback_exceptions = True

app.layout = get_layout(app, data)

@app.callback(
    dash.dependencies.Output("ens-output-container", "children"),
    [dash.dependencies.Input("ens-switch", "value")]
)
def update_ensemble(value):
    d = {True: "CanRCM4 Ensemble Mean", False: "HSM Recosntruction"}
    return f"{d[value]}"

@app.callback(
    dash.dependencies.Output("table", "children"),
    [dash.dependencies.Input("dropdown", "value")]
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
    [dash.dependencies.Input("toggle-switch", "value")]
)
def update_mask(value):
    d = {True: "ON", False: "OFF"}
    return f"Mask: {d[value]}"


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
    return f"Colorbar Range: {value[0]} to {value[1]}"

@app.callback(
    [
        Output(component_id="range-slider", component_property="min"),
        Output(component_id="range-slider", component_property="max"),
        Output(component_id="range-slider", component_property="step"),
        Output(component_id="range-slider", component_property="value")
    ],
    [Input(component_id="dropdown", component_property="value"),
    Input(component_id="slider", component_property="value")],
)
def update_slider(value, N):
    field = data[value]["reconstruction"][data[value]["dv"]].values
    minimum = np.round(np.nanmin(field), 3)
    maximum = np.round(np.nanmax(field), 3)
    step = (maximum-minimum)/(N+1)
    default = [minimum, maximum]
    return minimum, maximum, step, default


@app.callback(
    dash.dependencies.Output("slider-output-container", "children"),
    [dash.dependencies.Input("slider", "value")],
)
def update_slider_n(value):
    return f"N = {value}"

ds = data[list(data.keys())[0]]["reconstruction"]
# lxarr, lyarr, txarr, tyarr, ixmin, ixmax, iymin, iymax, plon, plat, prlon, prlat = gen_lines(ds, X, Y)

@app.callback(
    dash.dependencies.Output("my-graph", "figure"),
    [
        dash.dependencies.Input("toggle-switch", "value"),
        dash.dependencies.Input("toggle-station-switch", "value"),
        dash.dependencies.Input("dropdown", "value"),
        dash.dependencies.Input("slider", "value"),
        dash.dependencies.Input("range-slider", "value"),
        dash.dependencies.Input("ens-switch", "value")
    ],
)
def update_ds(
    toggle_value,
    toggle_station_value,
    dd_value,
    slider_value,
    range_slider,
    mean_button
):

    zmin = range_slider[0]
    zmax = range_slider[1]

    ticks = np.around(np.linspace(zmin, zmax, slider_value+1), 3)
    cmap = matplotlib.cm.get_cmap("viridis", slider_value)
    hexes = []
    for i in range(cmap.N):
        rgba = cmap(i)
        # rgb2hex accepts rgb or rgba
        hexes.append(matplotlib.colors.rgb2hex(rgba))

    dcolorsc = discrete_colorscale(ticks, hexes)
    ticktext = [f'{ticks[0]}-{ticks[1]}'] + [f'{ticks[k]}-{ticks[k+1]}' for k in range(1, len(ticks)-1)]

    r_or_m = "model" if mean_button else "reconstruction"

    dv, station_dv = data[dd_value]["dv"], data[dd_value]["station_dv"]
    ds = data[dd_value][r_or_m]
    df = data[dd_value]["stations"]

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

    if r_or_m == "model":
        mask = native_mask[iymin:iymax, ixmin:ixmax]
        ds_arr[~mask] = np.nan
    # print("CMAP", matplotlib_to_plotly("viridis", slider_value, zmax))
    cmap = matplotlib.cm.get_cmap("viridis", slider_value)
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
                    # colorscale=get_cmap_divisions("viridis", slider_value),
                    line=dict(width=0.35, color="DarkSlateGrey"),
                    showscale=False,
                ),
                hovertemplate="<b>Station Value: %{text}</b><br>",
                visible=toggle_station_value,
                name="",
            ),
        ]
    
    go_list += fig_list

    fig = {
        "data": go_list,
        "layout": {
            "title": f"<b>{dd_value}</b>",
            "font": dict(size=18, color='grey'),
            "xaxis": dict(
                zeroline=False, 
                range=[-24, 34],
                showgrid=False, # thin lines in the background
                visible=False  # numbers below
            ),
            "yaxis": dict(
                zeroline=False, 
                range=[-7.4, 37], 
                showgrid=False, # thin lines in the background
                visible=False
            ),
            'xaxis_showgrid': False, 
            'yaxis_showgrid': False,
            "hoverlabel": dict(
                bgcolor="white", font_size=16, font_family="Rockwell"
            ),
            "colorbar": dict(
                tickmode="array",
                # tickvals=ticks,
                ticktext=ticks
            ),
            "hoverdistance": 5,
            "hovermode": "closest",
            "width": 1000,
            "height": 750,
            "showlegend": True,
            "legend_orientation": "v",
            "scrollZoom": True,
        }
    }

    return fig


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=False)
