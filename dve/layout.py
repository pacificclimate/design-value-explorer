import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
import plotly.express as px
import numpy as np


def header(data):
    """
    Layout element for parts common to all tabs.
    Not actually a "header" so should probably be renamed or broken up into
    true header and other parts.
    """
    dd_options = [dict(label=name, value=name) for name in data.keys()]
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H1("Design Value Explorer"),
                    dcc.Dropdown(
                        id="dropdown",
                        options=dd_options,
                        value=list(data.keys())[0],
                        placeholder="Select a design value to display...",
                        searchable=True,
                        clearable=False,
                    ),
                    html.Br(),
                    html.Div(id="item-display"),
                ],
                style={"margin-left": "20px", "margin-right": "20px"},
            )
        ]
    )


def map_tab(data, colormaps):
    (first_dv,) = data[list(data.keys())[0]]["reconstruction"].data_vars
    first_rfield = data[list(data.keys())[0]]["reconstruction"][first_dv]
    dmin = np.nanmin(first_rfield)
    dmax = np.nanmax(first_rfield)
    num_range_slider_steps = 10

    return dcc.Tab(
        label="Map",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(id="my-graph")], align="center", width="auto"
                    ),
                    dbc.Col(
                        [
                            html.Div(html.H4("Overlay Options")),
                            dbc.Row(
                                [
                                    html.Div(
                                        id="ens-output-container",
                                        style={
                                            "align": "center",
                                            "marginRight": "1em",
                                        },
                                    ),
                                    html.Div(
                                        id="raster-output-container",
                                        style={
                                            "align": "center",
                                            "marginRight": "1em",
                                        },
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    html.Div(
                                        daq.ToggleSwitch(
                                            id="ens-switch", value=False
                                        ),
                                        style={
                                            "align": "center",
                                            "marginRight": "6.5em",
                                        },
                                    ),
                                    html.Div(
                                        daq.ToggleSwitch(
                                            id="raster-switch", value=True
                                        ),
                                        style={
                                            "align": "center",
                                            "marginRight": "1em",
                                        },
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    html.Div(
                                        id="mask-output-container",
                                        style={
                                            "align": "center",
                                            "marginRight": "1em",
                                        },
                                    ),
                                    html.Div(id="station-output-container"),
                                ]
                            ),
                            dbc.Row(
                                [
                                    html.Div(
                                        daq.ToggleSwitch(
                                            id="toggle-mask",
                                            size=50,
                                            value=True,
                                        ),
                                        style={
                                            "align": "center",
                                            "marginRight": "1em",
                                        },
                                    ),
                                    daq.ToggleSwitch(
                                        id="toggle-station-switch",
                                        size=50,
                                        value=False,
                                    ),
                                ]
                            ),
                            html.Div(html.H4("Colourbar Options")),
                            html.Div(html.P("Colour Map")),
                            dcc.Dropdown(
                                id="colorscale",
                                options=[
                                    {"value": x, "label": x} for x in colormaps
                                ],
                                value=None,
                            ),
                            dbc.Row([html.Div(id="log-output-container")]),
                            dbc.Row(
                                daq.ToggleSwitch(
                                    id="toggle-log", value=True, size=50
                                )
                            ),
                            dbc.Row(
                                [html.Div(id="cbar-slider-output-container")]
                            ),
                            dbc.Row(
                                html.Div(
                                    dcc.Slider(
                                        id="cbar-slider",
                                        min=2,
                                        max=30,
                                        step=1,
                                        value=10,
                                    ),
                                    style={"width": "500px"},
                                )
                            ),
                            dbc.Row(
                                html.Div(id="range-slider-output-container")
                            ),
                            dbc.Row(
                                html.Div(
                                    dcc.RangeSlider(
                                        id="range-slider",
                                        min=dmin,
                                        max=dmax,
                                        step=(dmax - dmin)
                                        / num_range_slider_steps,
                                        vertical=False,
                                        value=[dmin, dmax],
                                    ),
                                    style={"width": "500px"},
                                )
                            ),
                        ],
                        align="center",
                        width="auto",
                    ),
                ]
            )
        ],
    )


def table_C2_tab():
    return dcc.Tab(
        label="Table C-2",
        children=[
            html.H4("Reconstruction Values at Table C2 Locations"),
            html.Div(id="table"),
        ],
    )


def main(data, colormaps):

    # TODO: Replace this use of preloaded data with on-demand requests
    #   for the data to be loaded.

    # TODO: Remove? What were these for?
    # default_markers = np.linspace(dmin, dmax, N)

    return html.Div(
        id="big-app-container",
        children=[
            header(data),
            dcc.Tabs([map_tab(data, colormaps), table_C2_tab()]),
        ],
    )
