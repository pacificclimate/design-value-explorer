import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
import plotly.express as px
import numpy as np


def get_layout(app, data, colormaps):

    (first_dv, ) = data[list(data.keys())[0]]["reconstruction"].data_vars
    first_rfield = data[list(data.keys())[0]]["reconstruction"][first_dv]
    dmin = np.nanmin(first_rfield)
    dmax = np.nanmax(first_rfield)
    N = 10
    default_markers = np.linspace(dmin, dmax, N)
    dd_options = [dict(label=name, value=name) for name in data.keys()]

    app.layout = html.Div(
        id="big-app-container",
        children=[
                  dbc.Row([
                            dbc.Col([html.H1("Design Value Explorer"),
                                dcc.Dropdown(
                                    id="dropdown",
                                    options=dd_options,
                                    value=list(data.keys())[0],
                                    placeholder="Select a design value to display...",
                                    searchable=True,
                                    clearable=False,
                                ), 
                                html.Br(), 
                                html.Div(id="item-display")],
                                style={
                                        'margin-left' : '20px',
                                        'margin-right' : '20px'
                                        }
                                )
                            ]),
                  dcc.Tabs([
                        dcc.Tab(label='Map', children=[
                              dbc.Row([
                                        dbc.Col([dcc.Graph(id="my-graph"),], 
                                                align="center", width='auto'),
                                        dbc.Col([
                                                html.Div(html.H4('Overlay Options')),
                                                dbc.Row([
                                                    html.Div(id='ens-output-container', style={'border-width': 'thin'}),
                                                ]),
                                                dbc.Row([
                                                    daq.ToggleSwitch(id='ens-switch', value=False)
                                                ]),
                                                dbc.Row([
                                                    html.Div(id="mask-output-container", style={'align': 'center', 'marginRight': '1em'}),
                                                    html.Div(id="station-output-container")
                                                ]),
                                                dbc.Row([
                                                    html.Div(daq.ToggleSwitch(id="toggle-mask", size=50, value=True), style={'align': 'center', 'marginRight': '1em'}),
                                                    daq.ToggleSwitch( id="toggle-station-switch", size=50, value=False)
                                                ]),
                                                html.Div(html.H4('Colorbar Options')),
                                                dcc.Dropdown(
                                                    id='colorscale', 
                                                    options=[{"value": x, "label": x} 
                                                             for x in colormaps],
                                                    value=None
                                                ),
                                                dbc.Row([
                                                    html.Div(id="log-output-container"),
                                                    ]),
                                                dbc.Row(
                                                    daq.ToggleSwitch(id="toggle-log", value=False, size=50),
                                                ),
                                                dbc.Row([
                                                    html.Div(id="cbar-slider-output-container")
                                                    ]),
                                                dbc.Row(
                                                    html.Div(
                                                        dcc.Slider(
                                                            id="cbar-slider",
                                                            min=2,
                                                            max=30,
                                                            step=1,
                                                            value=10), style={'width': '500px'}
                                                        )
                                                ),
                                                dbc.Row(html.Div(id="range-slider-output-container")),
                                                dbc.Row(
                                                    html.Div(
                                                        dcc.RangeSlider(
                                                        id="range-slider",
                                                        min=dmin,
                                                        max=dmax,
                                                        step=(dmax-dmin)/N,
                                                        vertical=False,
                                                        value=[dmin, dmax],
                                                    ), style={'width': '500px'})
                                                ),
                                                ], align='center', width='auto')
                                ])
                    ]),
                    dcc.Tab(label='Table C-2', children=[
                            html.H4('Reconstruction Values at Table C2 Locations'),
                            html.Div(id="table")
                        ])
                    ])
            ])

    return app.layout