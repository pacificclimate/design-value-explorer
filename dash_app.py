import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import numpy as np
import xarray as xr

import matplotlib
from matplotlib import cm

import flask
import pandas as pd
import time
import os

from climpyrical.mask import *
from climpyrical.gridding import *
from climpyrical.datacube import *
import climpyrical as cp
from polygons import *
from colorbar import *

import yaml

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

with open("config.yml","r") as ymlfile:
    cfg = yaml.load(ymlfile)

# load polygon data
X, Y = load_north_america_polygons_plotly(cfg['polygon']['path'])

# create dict of field data from config
fields = [read_data(path, name) for path, name in list(zip(cfg['data']['fields']['paths'], cfg['data']['fields']['key_name_in_netcdf']))]
DS = dict(zip(cfg['data']['names'], fields))

def load_sftlf_mask(mask, dvmask):
    mask = mask.squeeze('time')
    mask = mask.drop('time')
    return mask[dvmask].values >= 1.0

MASK = {'mask': load_sftlf_mask(
    read_data(
        cfg['data']['mask']['paths'][0], 
        cfg['data']['mask']['key_name_in_netcdf'][0], 
        keys = ['rlon', 'rlat']),
         cfg['data']['mask']['key_name_in_netcdf'][0])
}

# create a dict of station data from config
stations = [pd.read_csv(path) for path in cfg['data']['stations']['paths']]
DF = dict(zip(cfg['data']['names'], stations))

# initialize app
server = flask.Flask('app')
server.secret_key = os.environ.get('secret_key', 'secret')

app = dash.Dash('app', server=server)

app.scripts.config.serve_locally = False

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

dd_options = [dict(label=name, value=name) for name in cfg['data']['names']]

strs = [str(val) for val in range(0, 20, 2)]
markers = dict(zip(list(range(0, 20, 2)), strs))

colorbar_params = [{name: 
                        {'minimum': cfg['data']['fields']['colorbar']['minimum'][i],
                         'maximum': cfg['data']['fields']['colorbar']['maximum'][i],
                         'step': cfg['data']['fields']['colorbar']['step'][i],
                         'default': cfg['data']['fields']['colorbar']['default'][i]}
                    } for i, name in enumerate(cfg['data']['names'])]

colorbar_params_dict = {}
for d in colorbar_params:
    colorbar_params_dict.update(d)

app.layout = html.Div(    
    id="big-app-container",
    children=[
            dbc.Row(
                [   
                    dbc.Col(
                        [
                            html.H1("National Building Code Design Value Explorer"),
                            dcc.Dropdown(
                                id='dropdown',
                                options=dd_options,
                                value=cfg['data']['names'][0],
                                placeholder="Select a design value to display...",
                                searchable=False,
                                clearable=False
                            ),
                            html.Br(),
                            html.Div(id='item-display'),
                            dcc.Graph(id = 'my-graph')
                        ], align='right', width='auto'
                    ),
                    dbc.Col(
                        [
                            html.Div(id='mask-output-container'),
                            daq.ToggleSwitch(
                                id='toggle-switch',
                                size=50,
                                value=False
                            ),
                            html.Div(id='slider-output-container'),
                            dcc.Slider(
                                id='slider',
                                min=2,
                                max=20,
                                step=1,
                                value=10,
                                marks=markers,
                                vertical=True
                            )
                        ], align="right", width=1
                    ),
                    dbc.Col([
                            html.Div(id='station-output-container'),
                            daq.ToggleSwitch(
                                id='toggle-station-switch',
                                size=50,
                                value=False
                            ),
                            html.Div(id='range-slider-output-container'),
                            dcc.RangeSlider(
                                id='range-slider',
                                min = -1,
                                max = 15,
                                step = 0.5,
                                vertical=True,
                                value=[0, 10]
                            ),
                        ], align="right", width=1
                    ),
                    dbc.Col([
                            html.Div(id='opacity-slider-output-container'),
                            dcc.Slider(
                                id='opacity-slider',
                                min = 0,
                                max = 1,
                                step = 0.05,
                                vertical=True,
                                value=0.9
                            ),
                        ], align="right", width=1
                    ),
                ],
                align='center'
            )
    ]
)

@app.callback(
    dash.dependencies.Output('mask-output-container', 'children'),
    [dash.dependencies.Input('toggle-switch', 'value')])
def update_mask(value):
    d = {True: 'ON', False: 'OFF'}
    return f'Mask: {d[value]}'

@app.callback(
    dash.dependencies.Output('station-output-container', 'children'),
    [dash.dependencies.Input('toggle-station-switch', 'value')])
def update_mask(value):
    d = {True: 'ON', False: 'OFF'}
    return f'Stations: {d[value]}'

@app.callback(
    dash.dependencies.Output('range-slider-output-container', 'children'),
    [dash.dependencies.Input('range-slider', 'value')])
def update_range(value):
    return f'{value[0]} to {value[1]}'

@app.callback(
    dash.dependencies.Output('opacity-slider-output-container', 'children'),
    [dash.dependencies.Input('opacity-slider', 'value')])
def update_opacity_range(value):
    return f'Opacity: {value}'

@app.callback(
    [Output(component_id='range-slider', component_property='min'),
     Output(component_id='range-slider', component_property='max'),
     Output(component_id='range-slider', component_property='step'),
     Output(component_id='range-slider', component_property='value')],
    [Input(component_id='dropdown', component_property='value')])    
def update_slider(selection):
    minimum = colorbar_params_dict[selection]['minimum']
    maximum = colorbar_params_dict[selection]['maximum']
    step = colorbar_params_dict[selection]['step']
    default = colorbar_params_dict[selection]['default']
    return minimum, maximum, step, default

@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('slider', 'value')])
def update_slider(value):
    return f'N = {value}'

@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [
        dash.dependencies.Input("toggle-switch", "value"),
        dash.dependencies.Input("toggle-station-switch", "value"),
        dash.dependencies.Input('dropdown', 'value'),
        dash.dependencies.Input('slider', 'value'),
        dash.dependencies.Input('range-slider', 'value'),
        dash.dependencies.Input('opacity-slider', 'value')
    ]
)
def update_ds(toggle_value, toggle_station_value, dd_value, slider_value, range_slider, opacity_value):

    zmin = range_slider[0]
    zmax = range_slider[1]

    dv, station_dv = values[dd_value], dd_value
    ds = DS[dd_value]
    df = DF[dd_value]

    ds_arr =  ds[dv].values.copy()
    rlon, rlat = ds.rlon.values, ds.rlat.values

    # clean up to include in original IO

    if toggle_value:
        mask = MASK['mask']
        ds_arr[0, ~mask] = np.nan

    source_crs={"init": "epsg:4326"}
    target_crs={
        "proj": "ob_tran",
        "o_proj": "longlat",
        "lon_0": -97,
        "o_lat_p": 42.5,
        "a": 6378137,
        "to_meter": 0.0174532925199,
        "no_defs": True
    }

    rlonx, rlaty = flatten_coords(rlon, rlat, ds)
    lon, lat = transform_coords(rlonx, rlaty, source_crs=target_crs, target_crs=source_crs)

    lon = lon.reshape((ds_arr.shape[1], ds_arr.shape[2]))
    lat = lat.reshape((ds_arr.shape[1], ds_arr.shape[2]))

    station_value = np.ones((ds_arr.shape[1], ds_arr.shape[2]), dtype=object)*'No Station'

    ix, iy = find_element_wise_nearest_pos(rlon, rlat, df.rlon.values, df.rlat.values)
    station_value[iy, ix] = df[station_dv].values

    fig = {'data': 
                [
                go.Scatter(
                    x=X,
                    y=Y,
                    mode='lines',
                  hoverinfo = 'none',
                  visible=True,
                  name="Borders",
                  line=dict(width=0.5, color='black')),
                go.Heatmap(
                    z=ds_arr[0, ...],
                    x=rlon,
                    y=rlat,
                    customdata=np.dstack((lon, lat, station_value)),
                    zmin=zmin,
                    zmax=zmax,
                    hoverongaps = True,
                    opacity=opacity_value,
                    colorscale=get_cmap_divisions('viridis', slider_value),
                    hovertemplate =
                    "<b>Design Value: %{z} </b> <br>" +
                    "<b>Station Value: %{customdata[2]}</b> <br>" +
                    "rlon: %{x}<br>" +
                    "rlat: %{y}<br>" +
                    "lon: %{customdata[0]}<br>" +
                    "lat: %{customdata[1]}<br>",
                    name="Reconstruction"
                ),
                go.Scatter(
                    x=df.rlon.values, 
                    y=df.rlat.values,
                    mode='markers',
                    marker=dict(
                    symbol='x',
                    color=df[station_dv].values, 
                    colorscale=get_cmap_divisions('viridis', slider_value),
                    line=dict(width=0.35, color='DarkSlateGrey'),
                    showscale=False,
                    ),
                    hoverinfo='skip',
                    visible=toggle_station_value,
                    name="Stations"
                )
            ],
            'layout':
            {    
                'title':f'<b>{dd_value}</b>',
                'font':dict(size=24),
                'xaxis':dict(range=[-30, 30]),
                'yaxis':dict(range=[-30, 30]),
                'hoverlabel':dict(
                    bgcolor="white", 
                    font_size=16, 
                    font_family="Rockwell"),
                'width':1000, 
                'height':750,
                'showlegend':True,
                'legend_orientation':"v",
                'scrollZoom': True
            }
        }

    return fig

if __name__ == '__main__':
    app.run_server()
