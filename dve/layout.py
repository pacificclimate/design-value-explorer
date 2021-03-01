import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
import plotly.express as px
import numpy as np
from dve.utils import sigfigs


def header(config):
    """
    Layout element for parts common to all tabs.
    Not actually a "header" so should probably be renamed or broken up into
    true header and other parts.

    Returns a list of rows.
    """
    dd_options = [
        {"label": f'{name} [{defn["description"]}]', "value": name}
        for name, defn in config["dvs"].items()
    ]
    return [
        dbc.Row(dbc.Col(html.H1("Design Value Explorer"))),
        dbc.Row(
            [
                dbc.Col(html.Label("Design Value"), width=1),
                dbc.Col(
                    dcc.Dropdown(
                        id="design-value-id-ctrl",
                        options=dd_options,
                        value=config["ui"]["defaults"]["dv"],
                        placeholder="Select a design value to display...",
                        searchable=True,
                        clearable=False,
                    ),
                    width=3,
                )
            ]
        )
    ]


def overlay_options():
    """
    Layout for Overlay Options section.
    This function returns a list of rows.
    """
    
    return [
        # Section title
        dbc.Row(dbc.Col(html.H4("Overlay Options"))),

        # Control titles
        dbc.Row(
            [
                dbc.Col(html.Label("Dataset"), width=6),
                dbc.Col(html.Label("Raster")),
                dbc.Col(html.Label("Mask")),
                dbc.Col(html.Label("Stations")),
            ]
        ),

        # Controls
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="dataset-ctrl",
                        options=[
                            {"label": "HSM Reconstruction", "value": "reconstruction"},
                            {"label": "CanRCM4 Ensemble Mean", "value": "model"},
                        ],
                        value="reconstruction",
                        clearable=False,
                    ),
                    width=6,
                ),
                dbc.Col(
                    daq.BooleanSwitch(
                        id="raster-ctrl", on=True
                    ),
                ),
                dbc.Col(
                    daq.BooleanSwitch(
                        id="mask-ctrl",
                        on=True,
                    ),
                ),
                dbc.Col(
                    daq.BooleanSwitch(
                        id="stations-ctrl",
                        on=False,
                    ),
                ),
            ]
        ),
    ]


def colourbar_options(data, colormaps):
    """
    Layout for Colourbar Options section.
    This function returns a list of rows.
    """
    
    (first_dv,) = data[list(data.keys())[0]]["reconstruction"].data_vars
    first_rfield = data[list(data.keys())[0]]["reconstruction"][first_dv]
    dmin = np.nanmin(first_rfield)
    dmax = np.nanmax(first_rfield)
    num_range_slider_steps = 10

    return [
        # Section title
        # TODO: Improve title -- something like Colour Scale Options
        dbc.Row(
            dbc.Col(html.H4("Colourbar Options")),
            # TODO: Replace with class
            style={"margin-top": "2.5em"},
        ),
        
        # Control titles
        dbc.Row(
            [
                dbc.Col(html.Label("Colour Map")),
                dbc.Col(html.Label("Scale")),
                dbc.Col(html.Label("Num. Colours")),
                dbc.Col(html.Label(id="range-slider-output-container")),
            ]
        ),
        
        # Controls
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="colour-map-ctrl",
                        options=[
                            {"value": x, "label": x} for x in colormaps
                        ],
                        value=None,
                    )
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="scale-ctrl",
                        options=[
                            {"label": "Linear", "value": "linear"},
                            {"label": "Logarithmic", "value": "logarithmic"},
                        ],
                        value="logarithmic",
                        clearable=False,
                    )
                ),
                dbc.Col(
                    daq.Slider(
                        id="cbar-slider",
                        min=2,
                        max=30,
                        step=1,
                        value=10,
                        size=150,
                        handleLabel={
                            "showCurrentValue": True,
                            "label": " ",
                            "style": {"font-size": "0.8em", "color": "black"},
                        },
                        marks={x: str(x) for x in (2, 30)},
                    ),
                    style={"padding-top": "2em"},
                ),
                dbc.Col(
                    html.Div(
                        dcc.RangeSlider(
                            # TODO: Rename
                            id="range-slider",
                            min=dmin,
                            max=dmax,
                            step=(dmax - dmin)
                                 / num_range_slider_steps,
                            vertical=False,
                            value=[dmin, dmax],
                            marks={
                                x: str(sigfigs(x))
                                for x in (dmin*1.008, (dmin + dmax) / 2, dmax)
                            }
                        ),
                        # RangeSlider has unwanted horiz padding of 25px.
                        style={"margin": "2em -25px"},
                    ),
                ),
            ]
        ),
    ]


def user_graph_interaction():
    """
    Layout for user graph interaction elements.
    :return: list of dbc.Row
    """
    return [
        dbc.Row([
            dbc.Col(
                html.Div(
                    id="hover-output",
                    children=[
                        dcc.Markdown("**Hover Data**"),
                        html.Div(id="hover-info"),
                        html.Pre(id="hover-data")
                    ]
                )
            ),
            dbc.Col(
                html.Div(
                    id="click-output",
                    children=[
                        dcc.Markdown("**Click Data**"),
                        html.Div(id="click-info"),
                        html.Pre(id="click-data")
                    ]
                )
            ),
        ]),
    ]


def map_tab(config, data):
    """
    Top-level layout of map tab.

    :param config:
    :param data:
    :return: dbc.Tab
    """
    colormaps = config["colormaps"]
    # Add reverse options, too
    cmap_r = tuple(f"{color}_r" for color in colormaps)
    colormaps += cmap_r

    return dbc.Tab(
        label="Map",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(id="my-graph")], align="center", width=7
                    ),
                    dbc.Col(
                        [
                            *overlay_options(),
                            *colourbar_options(data, colormaps),
                            *user_graph_interaction(),
                        ],
                        align="center",
                        width=5,
                    ),
                ]
            )
        ],
    )


def table_C2_tab():
    return dbc.Tab(
        label="Table C-2",
        children=[
            html.H4("Reconstruction Values at Table C2 Locations"),
            html.Div(id="table"),
        ],
    )


def main(config, data):
    """
    Top-level layout component. `app.layout` should be set to the this value.
    """

    # TODO: Replace the use of preloaded data with on-demand requests
    #   for the data to be loaded.

    return dbc.Container(
        id="big-app-container",
        fluid=True,
        style={"padding": "0.5em 1em 0"},
        children=[
            *header(config),
            dbc.Row(
                dbc.Col(
                    dbc.Tabs([map_tab(config, data), table_C2_tab()]),
                ),
                style={"margin-top": "1em"},
            ),
        ],
    )
