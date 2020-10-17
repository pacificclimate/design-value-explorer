from climpyrical.data import read_data
from climpyrical.gridding import flatten_coords, transform_coords, find_nearest_index
from polygons import load_north_america_polygons_plotly
from colorbar import get_cmap_divisions
from processing import coord_prep

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import numpy as np
import matplotlib.cm

import flask
import pandas as pd
import os

import yaml


with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

# load polygon data
X, Y = load_north_america_polygons_plotly(cfg["polygon"]["path"])

# create dict of field data from config
fields = [
    read_data(path)
    for path in list(
            cfg["data"]["fields"]["paths"]
    )
]
DS = dict(zip(cfg["data"]["names"], fields))

# create dict of data names and its corresponding key
KEYS = dict(
    zip(cfg["data"]["names"], cfg["data"]["fields"]["key_name_in_netcdf"])
)

# load mask 
def load_sftlf_mask(mask, dvmask):
    mask = mask.squeeze("time")
    mask = mask.drop("time")
    return mask[dvmask].values >= 1.0

# create a mask dict
MASK = {
    "mask": read_data(
            cfg["data"]["mask"]["paths"][0],
            required_keys=["rlon", "rlat"],
        )[cfg["data"]["mask"]["key_name_in_netcdf"][0]] >= 1.
}

# MASK['mask'] = MASK['mask'] >= 1.

# create a dict of station data from config
stations = [pd.read_csv(path) for path in cfg["data"]["stations"]["paths"]]
DF = dict(zip(cfg["data"]["names"], stations))

# initialize app
server = flask.Flask("app")

app = dash.Dash("app", server=server)
external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Pacific Climate Impacts Consortium Design Value Explorer'

dd_options = [dict(label=name, value=name) for name in cfg["data"]["names"]]

strs = [str(val) for val in range(0, 20, 2)]
markers = dict(zip(list(range(0, 20, 2)), strs))

strs_opacity = [str(val) for val in np.arange(0.0, 1.0, 0.1)]
markers_opacity = dict(zip(list(np.arange(0, 1, 0.1)), strs_opacity))

colorbar_params = [
    {
        name: {
            "minimum": cfg["data"]["fields"]["colorbar"]["minimum"][i],
            "maximum": cfg["data"]["fields"]["colorbar"]["maximum"][i],
            "step": cfg["data"]["fields"]["colorbar"]["step"][i],
            "default": cfg["data"]["fields"]["colorbar"]["default"][i],
        }
    }
    for i, name in enumerate(cfg["data"]["names"])
]

colorbar_params_dict = {}
for d in colorbar_params:
    colorbar_params_dict.update(d)

app.layout = html.Div(
    id="big-app-container",
    children=[
              dbc.Row([
                        dbc.Col([html.H1("National Building Code Design Value Explorer"),
                            dcc.Dropdown(
                                id="dropdown",
                                options=dd_options,
                                value=cfg["data"]["names"][0],
                                placeholder="Select a design value to display...",
                                searchable=False,
                                clearable=False,
                            ), 
                            html.Br(), 
                            html.Div(id="item-display")])
                        ]),
              dbc.Row([
                        dbc.Col([
                                dcc.Graph(id="my-graph")], 
                                align="center", width='auto'),
                        dbc.Col([
                                html.Div(html.H4('Overlay Options')),
                                dbc.Row([
                                html.Div(dbc.Button('Ensemble Mean', id='mean-button'), style={'border-width': 'thin'}),
                                html.Div(dbc.Button('Reconstruction', id='recon-button'), style={'border-width': 'thick'})]),
                                dbc.Row([
                                    html.Div(id="mask-output-container", style={'align': 'center', 'marginRight': '1em'}),
                                    html.Div(id="station-output-container")
                                ]),
                                dbc.Row([

                                    html.Div(daq.ToggleSwitch(id="toggle-switch", size=50, value=True), style={'align': 'center', 'marginRight': '1em'}),
                                    daq.ToggleSwitch( id="toggle-station-switch", size=50, value=False)
                                ]),
                                html.Div(html.H4('Colorbar Options')),
                                dbc.Row(html.Div(id='mean-button-out')),
                                dbc.Row(html.Div(id="slider-output-container")),
                                dbc.Row(
                                    html.Div(
                                        dcc.Slider(
                                            id="slider",
                                            min=2,
                                            max=20,
                                            step=1,
                                            value=10,
                                            marks=markers), style={'width': '500px'})
                                ),
                                dbc.Row(html.Div(id="range-slider-output-container")),
                                dbc.Row(
                                    html.Div(
                                        dcc.RangeSlider(
                                        id="range-slider",
                                        min=-1,
                                        max=15,
                                        step=0.5,
                                        vertical=False,
                                        value=[0, 10],
                                    ), style={'width': '500px'})
                                ),
                                dbc.Row(html.Div(id="opacity-slider-output-container")),
                                dbc.Row(
                                    html.Div(
                                        dcc.Slider(
                                            id="opacity-slider",
                                            min=0,
                                            max=1,
                                            step=0.05,
                                            vertical=False,
                                            value=0.9,
                                            marks=markers_opacity
                                        ), style={'width': '500px'}
                                    )
                                )], align='center', width='auto')
                ])
            ],
)
@app.callback(Output('mean-button-out', 'children'),
              [Input('mean-button', 'n_clicks')])
def mean_button(click):
    # Check if toggle on or of
    click = 2 if click is None else click
    return True if click % 2 == 0 else None

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
def update_mask(value):
    d = {True: "ON", False: "OFF"}
    return f"Stations: {d[value]}"


@app.callback(
    dash.dependencies.Output("range-slider-output-container", "children"),
    [dash.dependencies.Input("range-slider", "value")]
)
def update_range(value):
    return f"Colorbar Range: {value[0]} to {value[1]}"


@app.callback(
    dash.dependencies.Output("opacity-slider-output-container", "children"),
    [dash.dependencies.Input("opacity-slider", "value")]
)
def update_opacity_range(value):
    return f"Opacity: {value}"


@app.callback(
    [
        Output(component_id="range-slider", component_property="min"),
        Output(component_id="range-slider", component_property="max"),
        Output(component_id="range-slider", component_property="step"),
        Output(component_id="range-slider", component_property="value")
    ],
    [Input(component_id="dropdown", component_property="value")],
)
def update_slider(selection):
    minimum = colorbar_params_dict[selection]["minimum"]
    maximum = colorbar_params_dict[selection]["maximum"]
    step = colorbar_params_dict[selection]["step"]
    default = colorbar_params_dict[selection]["default"]
    return minimum, maximum, step, default


@app.callback(
    dash.dependencies.Output("slider-output-container", "children"),
    [dash.dependencies.Input("slider", "value")],
)
def update_slider(value):
    return f"N = {value}"


@app.callback(
    dash.dependencies.Output("my-graph", "figure"),
    [
        dash.dependencies.Input("toggle-switch", "value"),
        dash.dependencies.Input("toggle-station-switch", "value"),
        dash.dependencies.Input("dropdown", "value"),
        dash.dependencies.Input("slider", "value"),
        dash.dependencies.Input("range-slider", "value"),
        dash.dependencies.Input("opacity-slider", "value"),
    ],
)
def update_ds(
    toggle_value,
    toggle_station_value,
    dd_value,
    slider_value,
    range_slider,
    opacity_value,
):

    zmin = range_slider[0]
    zmax = range_slider[1]

    dv, station_dv = KEYS[dd_value], dd_value
    ds = DS[dd_value]
    df = DF[dd_value]


    print(ds[dv].values.shape)
    ds_arr = ds[dv].values.copy()

    lon, lat, station_value_grid = coord_prep(ds, df, station_dv, dv)


    target_crs={'init': 'epsg:4326'}
    source_crs={'proj': 'ob_tran', 'o_proj': 'longlat', 'lon_0': -97, 'o_lat_p': 42.5, 'a': 6378137, 'to_meter': 0.0174532925199, 'no_defs': True}


    latlines = np.array([20, 45., 60, 75])
    lonlines = np.linspace(189.6, 336.4, 10)

    plon, plat = flatten_coords(lonlines, latlines)
    prlon, prlat = transform_coords(plon, plat)

    latliney = [np.ones(ds.rlon.values.size)*latline for latline in latlines]
    latlinex = np.linspace(189.6-10, 336.4+10, ds.rlon.values.size)

    lonlinex = [np.ones(lat.size)*lonline for lonline in lonlines]
    lonliney = np.linspace(20., 90, lat.size)

    lxarr, lyarr = [], []
    txarr, tyarr = [], []
    
    for lonline in lonlinex:
        lx, ly = transform_coords(lonline, lonliney)
        lx = np.append(lx[::10], None)
        ly = np.append(ly[::10], None)
        lxarr.append(lx)
        lyarr.append(ly)
        
    for latline in latliney:
        tx, ty = transform_coords(latlinex, latline)
        tx = np.append(tx[::10], None)
        ty = np.append(ty[::10], None)
        txarr.append(tx)
        tyarr.append(ty)

    # ticks = np.ones(np.array(txarr).shape, dtype=object)*""
    # none_mask = np.array(txarr) == None
    # ticks[none_mask] = latlines

    lxarr = np.array(lxarr).flatten()
    lyarr = np.array(lyarr).flatten()
    txarr = np.array(txarr).flatten()
    tyarr = np.array(tyarr).flatten()

    if toggle_value:
        mask = MASK["mask"]
        ds_arr[~mask] = np.nan

    lattext = [str(int(latval))+"N"+", "+str(int(360-lonval))+'W' for latval, lonval in zip(plat, plon)] 

    fig = {
        "data": [
            go.Scattergl(
                x=lxarr,
                y=lyarr,
                mode="lines",
                hoverinfo="skip",
                visible=True,
                name="lonlines",
                line=dict(width=1, color="grey", dash='dash'),
            ),
            go.Scattergl(
                x=txarr,
                y=tyarr,
                mode="lines+text",
                hoverinfo="skip",
                visible=True,
                name="latlines",
                line=dict(width=1, color="grey", dash='dash'),
            ),
            go.Scattergl(
                x=prlon,
                y=prlat,
                mode="text",
                text=lattext,
                hoverinfo="skip",
                visible=True
            ),
            go.Scattergl(
                x=X,
                y=Y,
                mode="lines",
                hoverinfo="skip",
                visible=True,
                name="",
                line=dict(width=0.5, color="black"),
            ),
            go.Heatmap(
                z=ds_arr,
                x=ds.rlon,
                y=ds.rlat,
                # contours=dict(
                #     coloring ='heatmap',
                #     showlabels = True, # show labels on contours
                #     labelfont = dict( # label font properties
                #         size = 12,
                #         color = 'white',
                #     )
                # ),
                customdata=np.dstack((lon, lat, station_value_grid)),
                zmin=zmin,
                zmax=zmax,
                # hoverongaps=True,
                # zsmooth = 'best',
                opacity=opacity_value,
                colorscale=get_cmap_divisions("viridis", slider_value),
                # hoverinfo="<b>Design Value: %{z} </b> <br>"
                # + "<b>Station Value: %{customdata[2]}</b> <br>"
                # + "rlon, rlat: %{x}, %{y}<br>"
                # + "lon, lat: %{customdata[0]}, %{customdata[1]}<br>",
                # name=""
            ),
            go.Scattergl(
                x=df.rlon.values,
                y=df.rlat.values,
                mode="markers",
                marker=dict(
                    symbol="x",
                    color=df[station_dv].values,
                    colorscale=get_cmap_divisions("viridis", slider_value),
                    line=dict(width=0.35, color="DarkSlateGrey"),
                    showscale=False,
                ),
                hoverinfo="skip",
                visible=toggle_station_value,
                name="",
            ),
        ],
        "layout": {
            "title": f"<b>{dd_value}</b>",
            "font": dict(size=8, color='grey'),
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
            "width": 1000,
            "height": 750,
            "showlegend": True,
            "legend_orientation": "v",
            "scrollZoom": True,
        }
    }

    return fig

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=True)
