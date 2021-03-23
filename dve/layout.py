import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
from dve.labelling_utils import dv_label

scale_ctrl_options = [
    {"label": "Linear", "value": "linear"},
    {"label": "Logarithmic", "value": "logarithmic"},
]


def header(config):
    """
    Layout element for parts common to all tabs.
    Not actually a "header" so should probably be renamed or broken up into
    true header and other parts.

    Returns a list of rows.
    """
    dd_options = [
        {
            "label": dv_label(
                config, design_value_id, with_units=False, with_description=True
            ),
            "value": design_value_id,
        }
        for design_value_id in config["ui"]["dvs"]
    ]
    return [
        dbc.Row(dbc.Col(html.H1("Design Value Explorer"))),
        dbc.Row(
            [
                dbc.Col(html.Label("Design Variable"), width=1),
                dbc.Col(
                    dcc.Dropdown(
                        id="design-value-id-ctrl",
                        options=dd_options,
                        value=config["ui"]["defaults"]["dv"],
                        searchable=True,
                        clearable=False,
                    ),
                    width=4,
                ),
            ]
        ),
    ]


def climate_regime_ctrl_options(config):
    return [
        {
            "label": config["ui"]["labels"]["climate_regime"][cr],
            "value": cr,
        }
        for cr in ("historical", "future")
    ]


def overlay_options(config):
    """
    Layout for Overlay Options section.
    This function returns a list of rows.
    """
    future_dataset_ctrl_options = [
        {
            "label": (
                config["ui"]["labels"]["future_change_factors"]["long"]
                    .format(id)
            ),
            "value": id,
        }
        for id in config["ui"]["future_change_factors"]
    ]

    climate_regime_ctrl_opts = climate_regime_ctrl_options(config)
    
    col_widths = (3, 3, 2, 2, 2)

    return [
        # Section title
        dbc.Row(dbc.Col(html.H5("Overlay Options")), className="mt-2"),
        # Control titles
        dbc.Row(
            [
                dbc.Col(html.Label(label), width=width) 
                for label, width in zip(
                    ("Climate", "Dataset", "Mask", "Stations", "Grid"), 
                    col_widths,
                )
            ],
        ),
        # Controls
        dbc.Row(
            [
                dbc.Col(control, width=width)
                for control, width in zip(
                    (
                        dcc.RadioItems(
                            id="climate-regime-ctrl",
                            options=climate_regime_ctrl_opts,
                            value=climate_regime_ctrl_opts[0]["value"],
                            labelStyle={"display": "block", "margin-top": "1em"},
                        ),
                        [
                            dcc.Dropdown(
                                id="historical-dataset-ctrl",
                                options=[
                                    {
                                        "label": "HSM Reconstruction",
                                        "value": "reconstruction",
                                    },
                                    {
                                        "label": "CanRCM4 Ensemble Mean",
                                        "value": "model",
                                    },
                                ],
                                value="reconstruction",
                                clearable=False,
                            ),
                            dcc.Dropdown(
                                id="future-dataset-ctrl",
                                options=future_dataset_ctrl_options,
                                value=future_dataset_ctrl_options[0]["value"],
                                disabled=True,
                                clearable=False,
                            ),
                        ],
                        daq.BooleanSwitch(
                            id="mask-ctrl", on=True, style={"width": "50px"}
                        ),
                        daq.BooleanSwitch(
                            id="stations-ctrl",
                            on=False,
                            style={"width": "100px"},
                            label={
                                "label": "(HISTORICAL ONLY)",
                                "style": {
                                    "font-size": "0.8em",
                                    "font-style": "italic",
                                }
                            },
                            labelPosition="bottom",
                        ),
                        daq.BooleanSwitch(
                            id="grid-ctrl",
                            on=True,
                            style={"width": "50px"},
                        ),
                    ),
                    col_widths,
                )
            ],
            style={"font-size": "0.8em"},
        ),
    ]


def colourbar_options(config):
    """
    Layout for Colourbar Options section.
    This function returns a list of rows.
    """
    colour_maps = config["map"]["colour_maps"]
    # Add reverse options, too
    cmap_r = tuple(f"{color}_r" for color in colour_maps)
    colour_maps += cmap_r

    return [
        # Section title
        dbc.Row(
            dbc.Col(html.H5("Colour Scale Options")),
            # TODO: Replace with class
            className="mt-5",
        ),
        # Control titles
        dbc.Row(
            [
                dbc.Col(html.Label("Colour Map")),
                dbc.Col(html.Label("Scale")),
                dbc.Col(html.Label("Num. Colours")),
                dcc.Loading(
                    dbc.Col(
                        html.Label(id="colourbar-range-ctrl-output-container"),
                    ),
                    **config["ui"]["loading"],
                ),
            ]
        ),
        # Controls
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="colour-map-ctrl",
                        options=[{"value": x, "label": x} for x in colour_maps],
                        value=None,
                    )
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="scale-ctrl",
                        options=scale_ctrl_options,
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
                    dcc.Loading(
                        html.Div(
                            dcc.RangeSlider(id="colourbar-range-ctrl"),
                            # RangeSlider has unwanted horiz padding of 25px.
                            style={"margin": "2em -25px"},
                        ),
                        **config["ui"]["loading"],
                    )
                ),
            ],
            style={"font-size": "0.8em"},
        ),
    ]


def user_graph_interaction(config):
    """
    Layout for user graph interaction elements.
    :return: list of dbc.Row
    """
    return [
        dbc.Row(
            dbc.Col(
                [
                    html.H5("Data from map pointer"),
                    dcc.Markdown(
                        "*Hover over map to show position of cursor. "
                        "Click to hold design values for download.*",
                        style={"font-size": "0.8em"},
                    ),
                ]
            )
        ),
        dbc.Row(
            [dbc.Col(id="data-download-header", width={"size": 9, "offset": 3})]
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        id="hover-output",
                        children=[
                            html.Div(
                                id="hover-info", style={"font-size": "0.8em"}
                            ),
                            html.Pre(id="hover-data"),
                        ],
                    ),
                    width=3,
                ),
                dbc.Col(
                    dcc.Loading(
                        html.Div(
                            id="click-output",
                            children=[
                                html.Div(
                                    id="click-info",
                                    style={"font-size": "0.8em"},
                                ),
                                html.Pre(id="click-data"),
                            ],
                        ),
                        **config["ui"]["loading"],
                    ),
                    width=9,
                ),
            ]
        ),
    ]


def map_tab(config):
    """
    Top-level layout of map tab.

    :param config:
    :return: dbc.Tab
    """
    return dbc.Tab(
        label="Map",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            dcc.Graph(
                                id="my-graph",
                                config=config["ui"]["graph"],
                            ),
                            **config["ui"]["loading"],
                        ),
                        lg=7,
                        md=12,
                        sm=12,
                        xs=12,
                    ),
                    dbc.Col(
                        [
                            *overlay_options(config),
                            *colourbar_options(config),
                            *user_graph_interaction(config),
                        ],
                        lg=5,
                        md=12,
                        sm=12,
                        xs=12,
                    ),
                ],
                align="start",
            )
        ],
    )


def table_C2_tab(config):
    return dbc.Tab(
        label="Table C-2",
        children=dcc.Loading(
            [
                html.H5(
                    id="table-C2-title",
                    className="mt-3",
                ),
                html.Div(id="table-C2"),
            ],
            **config["ui"]["loading"],
        ),
    )


def internal_data():
    """
    Layout components for storing/sharing data between callbacks (and callback
    invocations) on the client side, using a hidden div (ick!). See
    https://dash.plotly.com/sharing-data-between-callbacks.

    :return: List of components.
    """
    return [html.Div(id="viewport-ds", style={"display": "none"})]


def main(config):
    """
    Top-level layout component. `app.layout` should be set to the this value.
    """
    return dbc.Container(
        id="big-app-container",
        fluid=True,
        style={"padding": "0.5em 1em 0"},
        children=[
            *header(config),
            dbc.Row(
                dbc.Col(dbc.Tabs([map_tab(config), table_C2_tab(config)])),
                style={"margin-top": "1em"},
            ),
            *internal_data(),
        ],
    )
