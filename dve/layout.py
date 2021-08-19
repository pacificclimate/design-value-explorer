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

        cfg = config["ui"]["labels"]["overlay-options"]

        return [
            # Section title
            dbc.Row(dbc.Col(html.H5(cfg["title"])), className="mt-2"),
            # Control titles
            dbc.Row(
                [
                    dbc.Col(html.Label(column["title"]), width=column["width"])
                    for column in cfg["columns"]
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
                        [column["width"] for column in cfg["columns"]],
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

        cfg = config["ui"]["labels"]["colorscale-options"]

        # Controls by column key in config
        controls = {
            "color-map": dcc.Dropdown(
                id="color_map",
                options=[{"value": x, "label": x} for x in colour_maps],
                **config["ui"]["controls"]["colour-map"],
            ),
            "scale": dcc.Dropdown(
                id="color_scale_type",
                options=scale_ctrl_options,
                **config["ui"]["controls"]["scale"],
            ),
            "num-colors": html.Div(
                daq.Slider(
                    id="num_colors", **config["ui"]["controls"]["num-colours"]
                ),
                style={"padding-top": "2em"},
            ),
            "range": Loading(
                html.Div(
                    dcc.RangeSlider(
                        id="color_scale_data_range",
                        **config["ui"]["controls"]["colourbar-range"],
                    ),
                    # RangeSlider has unwanted horiz padding of 25px.
                    style={"margin": "2em -25px"},
                )
            ),
        }

        return [
            # Section title
            dbc.Row(dbc.Col(html.H5(cfg["title"])), className="mt-5"),
            # Control titles
            dbc.Row(
                [
                    dbc.Col(
                        Loading(
                            html.Label(
                                column["title"],
                                id=f"colorscale_options_label_{col_key}",
                            )
                        ),
                        width=column["width"],
                    )
                    for col_key, column in (
                        (col_id, cfg["columns"][col_id])
                        for col_id in cfg["column-order"]
                    )
                ]
            ),
            # Controls
            dbc.Row(
                [
                    dbc.Col(controls[col_key], width=column["width"])
                    for col_key, column in (
                        (col_id, cfg["columns"][col_id])
                        for col_id in cfg["column-order"]
                    )
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
            label=config["ui"]["labels"]["main_tabs"]["map-tab"],
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        Loading(
                                            dcc.Graph(
                                                id="map_main_graph",
                                                config=config["ui"]["graph"],
                                            )
                                        ),
                                        lg=11,
                                    ),
                                    dbc.Col(
                                        Loading(
                                            dcc.Graph(
                                                id="map_colorscale_graph",
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
            label=config["ui"]["labels"]["main_tabs"]["table-tab"],
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
        fluid=True,
        style={"padding": "0.5em 1em 0"},
        children=[
            *header(),
            dbc.Row(
                dbc.Col(
                    dbc.Tabs(
                        id="main_tabs",
                        children=[map_tab(), table_C2_tab()],
                        active_tab=config["ui"]["controls"]["main_tabs"][
                            "active-tab"
                        ],
                    )
                ),
                style={"margin-top": "1em"},
            ),
            *internal_data(),
        ],
    )
