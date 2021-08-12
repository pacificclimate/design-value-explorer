import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
from dve.config import dv_label

scale_ctrl_options = [
    {"label": "Linear", "value": "linear"},
    {"label": "Logarithmic", "value": "logarithmic"},
]


def climate_regime_ctrl_options(config, which="long"):
    return [
        {
            "label": config["ui"]["labels"]["climate_regime"][cr][which],
            "value": cr,
        }
        for cr in ("historical", "future")
    ]


def main(config):
    """
    Top-level layout component. `app.layout` should be set to what this function
    returns.
    """

    def Loading(*args, **kwargs):
        """
        Add loading config to a dcc.Loading call.
        """
        return dcc.Loading(*args, **kwargs, **config["ui"]["loading"])

    def header():
        """
        Layout element for parts common to all tabs.
        Not actually a "header" so should probably be renamed or broken up into
        true header and other parts.

        Returns a list of rows.
        """
        dd_options = [
            {
                "label": dv_label(
                    config,
                    design_variable,
                    with_units=False,
                    with_description=True,
                ),
                "value": design_variable,
            }
            for design_variable in config["ui"]["dvs"]
        ]
        return [
            dbc.Row(dbc.Col(html.H1("Design Value Explorer"))),
            dbc.Row(
                [
                    dbc.Col(html.Label("Design Variable"), width=1),
                    dbc.Col(
                        dcc.Dropdown(
                            id="design_variable",
                            options=dd_options,
                            **config["ui"]["controls"]["design-value-id"],
                        ),
                        width=4,
                    ),
                ]
            ),
        ]

    def overlay_options():
        """
        Layout for Overlay Options section.
        This function returns a list of rows.
        """
        future_dataset_ctrl_options = [
            {
                "label": (
                    config["ui"]["labels"]["future_change_factors"][
                        "long"
                    ].format(id)
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
                        # TODO: Get from config
                        ("Period", "Dataset", "Mask", "Stations", "Grid"),
                        col_widths,
                    )
                ]
            ),
            # Controls
            dbc.Row(
                [
                    dbc.Col(control, width=width)
                    for control, width in zip(
                        (
                            dcc.RadioItems(
                                id="climate_regime",
                                options=climate_regime_ctrl_opts,
                                **config["ui"]["controls"]["climate-regime"],
                            ),
                            [
                                dcc.Dropdown(
                                    id="historical_dataset_id",
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
                                    **config["ui"]["controls"][
                                        "historical-dataset"
                                    ],
                                ),
                                dcc.Dropdown(
                                    id="future_dataset_id",
                                    options=future_dataset_ctrl_options,
                                    **config["ui"]["controls"][
                                        "future-dataset"
                                    ],
                                ),
                            ],
                            daq.BooleanSwitch(
                                id="apply_mask",
                                **config["ui"]["controls"]["mask"],
                            ),
                            daq.BooleanSwitch(
                                id="show_stations",
                                **config["ui"]["controls"]["stations"],
                            ),
                            daq.BooleanSwitch(
                                id="show_grid",
                                **config["ui"]["controls"]["grid"],
                            ),
                        ),
                        col_widths,
                    )
                ],
                style={"font-size": "0.8em"},
            ),
        ]

    def colourbar_options():
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
            dbc.Row(dbc.Col(html.H5("Colour Scale Options")), className="mt-5"),
            # Control titles
            dbc.Row(
                [
                    dbc.Col(html.Label("Colour Map")),
                    dbc.Col(html.Label("Scale")),
                    dbc.Col(html.Label("Num. Colours")),
                    Loading(
                        dbc.Col(
                            html.Label(
                                id="colorscale_range_label"
                            )
                        )
                    ),
                ]
            ),
            # Controls
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            id="color_map",
                            options=[
                                {"value": x, "label": x} for x in colour_maps
                            ],
                            **config["ui"]["controls"]["colour-map"],
                        )
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="color_scale_type",
                            options=scale_ctrl_options,
                            **config["ui"]["controls"]["scale"],
                        )
                    ),
                    dbc.Col(
                        daq.Slider(
                            id="num_colors",
                            **config["ui"]["controls"]["num-colours"],
                        ),
                        style={"padding-top": "2em"},
                    ),
                    dbc.Col(
                        Loading(
                            html.Div(
                                dcc.RangeSlider(
                                    id="color_scale_data_range",
                                    **config["ui"]["controls"][
                                        "colourbar-range"
                                    ],
                                ),
                                # RangeSlider has unwanted horiz padding of 25px.
                                style={"margin": "2em -25px"},
                            )
                        )
                    ),
                ],
                style={"font-size": "0.8em"},
            ),
        ]

    def user_graph_interaction():
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
                [
                    dbc.Col(
                        id="data-download-header",
                        width={"size": 9, "offset": 3},
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="map_hover_output",
                            children=[
                                html.Div(
                                    id="map_hover_info",
                                    style={"font-size": "0.8em"},
                                ),
                                html.Pre(id="map_hover_data"),
                            ],
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        Loading(
                            html.Div(
                                id="map_click_output",
                                children=[
                                    html.Div(
                                        id="map_click_info",
                                        style={"font-size": "0.8em"},
                                    ),
                                    html.Pre(id="map_click_data"),
                                ],
                            )
                        ),
                        width=9,
                    ),
                ]
            ),
        ]

    def map_tab():
        """
        Top-level layout of map tab.

        :param config:
        :return: dbc.Tab
        """
        return dbc.Tab(
            tab_id="map-tab",
            label="Map",
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        Loading(
                                            dcc.Graph(
                                                id="my-graph",
                                                config=config["ui"]["graph"],
                                            )
                                        ),
                                        lg=11,
                                    ),
                                    dbc.Col(
                                        Loading(
                                            dcc.Graph(
                                                id="my-colorscale",
                                                config={
                                                    "displayModeBar": False
                                                },
                                            )
                                        ),
                                        lg=1,
                                    ),
                                ]
                            ),
                            lg=7,
                            md=12,
                            sm=12,
                            xs=12,
                        ),
                        dbc.Col(
                            [
                                *overlay_options(),
                                *colourbar_options(),
                                *user_graph_interaction(),
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

    def table_C2_tab():
        return dbc.Tab(
            tab_id="table-tab",
            label="Table C-2",
            children=[
                Loading(html.H5(id="table-C2-title", className="mt-3")),
                Loading(html.Div(id="table-C2")),
            ],
        )

    def internal_data():
        """
        Layout components for storing/sharing data between callbacks (and callback
        invocations) on the client side, using a hidden div (ick!). See
        https://dash.plotly.com/sharing-data-between-callbacks.

        :return: List of components.
        """
        return [
            html.Div(
                id="viewport-ds", style={"display": "none"}, children="null"
            )
        ]

    return dbc.Container(
        id="big-app-container",
        fluid=True,
        style={"padding": "0.5em 1em 0"},
        children=[
            *header(),
            dbc.Row(
                dbc.Col(
                    dbc.Tabs(
                        id="tabs",
                        children=[map_tab(), table_C2_tab()],
                        active_tab="map-tab",
                    )
                ),
                style={"margin-top": "1em"},
            ),
            *internal_data(),
        ],
    )
