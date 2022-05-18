import os
from copy import deepcopy
from dash import html
import dash_bootstrap_components as dbc
from dash import dcc
import dash_daq as daq
from dve.config import (
    dv_label, climate_regime_ctrl_options, overlay_options_stations_label,
    overlay_options_section_title,
    overlay_options_control_columns, color_map_ctrl_options, scale_ctrl_options,
    colourbar_options_section_title, color_bar_options_ctrl_width,
    color_bar_options_ctrl_title, map_tab_label, table_c2_label, help_tab_label,
    help_subtab_label, help_subtab_content, about_tab_label, about_subtab_label,
    about_subtab_card_spec, future_change_factor_label,
)
from dve.dict_utils import path_set


def interpret(source):
    os.environ["DVE_VERSION_TAG_ONLY"] = os.environ["DVE_VERSION"].split()[0]
    return dcc.Markdown(
        source.format(**os.environ), dangerously_allow_html=True
    )


def compact(iterable):
    return list(filter(None, iterable))


def card_item(card):
    color = card.get("color")
    title = card.get("title")
    header = card.get("header")
    body = card.get("body")
    return dbc.Card(
        className="me-3 mb-3 float-start",
        style={"width": "30%"},
        color=color,
        children=compact(
            (
                header and dbc.CardHeader(interpret(header)),
                title and html.H4(interpret(title), className="card-title"),
                body and dbc.CardBody(interpret(body)),
            )
        ),
    )


def card_set(cards, row_args={}, col_args={}):
    return dbc.Row(dbc.Col([card_item(card) for card in cards]), **row_args)
    return dbc.Row(
        [dbc.Col(card_item(card), **col_args) for card in cards], **row_args
    )


def main(app, config, lang="en"):
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
                    config, lang,
                    design_variable,
                    with_units=False,
                    with_description=True,
                ),
                "value": design_variable,
            }
            for design_variable in config["ui"]["dvs"]
        ]
        return [
            dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            html.Img(src=app.get_asset_url("pcic-logo.png")),
                            href="https://pacificclimate.org/",
                            target="_blank",
                            title="Pacific Climate Impacts Consortium website",
                        ),
                        xs=6,
                        className="align-self-center text-end",
                    ),
                    dbc.Col(
                        html.A(
                            "Design Value Explorer",
                            href=app.get_relative_path("/"),
                            style={
                                "font-size": "2em",
                                "color": "inherit",
                                "text-decoration": "none",
                            },
                        ),
                        xs=6,
                        className="align-self-center text-start",
                    ),
                ],
                className="pb-1 mb-3 border-bottom",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Label("Design Variable"),
                        xs=12,
                        md=3,
                        lg=2,
                        xxl=1,
                        className="align-self-center",
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="design_variable",
                            options=dd_options,
                            **config["ui"]["controls"]["design-value-id"],
                        ),
                        xs=12,
                        md=9,
                        lg=6,
                        xxl=4,
                        className="align-self-center",
                    ),
                    dbc.Col(html.A()),
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
                "label": future_change_factor_label(
                    config, lang, dataset_id, which="long"
                ),
                "value": dataset_id,
            }
            for dataset_id in config["ui"]["future_change_factors"]
        ]

        return [
            # Section title
            dbc.Row(dbc.Col(html.H5(overlay_options_section_title(config, lang)))),
            # Control titles
            dbc.Row(
                [
                    dbc.Col(html.Label(title), width=width)
                    for title, width in overlay_options_control_columns(config, lang)
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
                                options=climate_regime_ctrl_options(config, lang),
                                **config["ui"]["controls"]["climate-regime"],
                            ),
                            html.Div(
                                id="global_warming",
                                children=[
                                    html.Div(style={"height": "2.5em"}),
                                    dcc.Dropdown(
                                        id="future_dataset_id",
                                        options=future_dataset_ctrl_options,
                                        **config["ui"]["controls"][
                                            "future-dataset"
                                        ],
                                    ),
                                ],
                                **config["ui"]["controls"]["global_warming"],
                            ),
                            daq.BooleanSwitch(
                                id="show_stations",
                                # This is a cheap and nasty way to merge a value
                                # into an existing dict.
                                **path_set(
                                    deepcopy(
                                        config["ui"]["controls"]["stations"]
                                    ),
                                    "label.label",
                                    overlay_options_stations_label(config, lang),
                                ),
                            ),
                            daq.BooleanSwitch(
                                id="show_grid",
                                **config["ui"]["controls"]["grid"],
                            ),
                        ),
                        [
                            width
                            for title, width in overlay_options_control_columns(config, lang)
                        ],
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

        cfg = config["ui"]["labels"][lang]["colorscale-options"]

        # Controls by column key in config
        controls = {
            "color-map": dcc.Dropdown(
                id="color_map",
                options=color_map_ctrl_options(config, lang),
                **config["ui"]["controls"]["colour-map"],
            ),
            "scale": dcc.Dropdown(
                id="color_scale_type",
                options=scale_ctrl_options(config, lang),
                **config["ui"]["controls"]["scale"],
            ),
            "num-colors": html.Div(
                daq.Slider(
                    id="num_colors", **config["ui"]["controls"]["num-colours"]
                ),
                style={"padding-top": "3em"},
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
            dbc.Row(dbc.Col(html.H5(colourbar_options_section_title(config, lang)))),
            # Control titles
            dbc.Row(
                [
                    dbc.Col(
                        Loading(
                            html.Label(
                                color_bar_options_ctrl_title(config, lang, col_key),
                                id=f"colorscale_options_label_{col_key}",
                            )
                        ),
                        width=color_bar_options_ctrl_width(config, lang, col_key),
                    )
                    for col_key in cfg["column-order"]
                ]
            ),
            # Controls
            dbc.Row(
                [
                    dbc.Col(
                        controls[col_key],
                        width=color_bar_options_ctrl_width(config, lang, col_key)
                    )
                    for col_key in cfg["column-order"]
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
            label=map_tab_label(config, lang),
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            overlay_options(),
                            xxl={"size": 6, "order": 1},
                            xs=12,
                            className="pt-3 pb-3",
                        ),
                        dbc.Col(
                            colourbar_options(),
                            xxl={"size": 6, "order": 1},
                            xs=12,
                            className="pt-3 pb-3",
                        ),
                        dbc.Col(
                            Loading(
                                dcc.Graph(
                                    id="map_main_graph",
                                    config=config["ui"]["graph"],
                                )
                            ),
                            xxl={"size": 7, "order": 3},
                            xs=12,
                            className="border-top",
                        ),
                        dbc.Col(
                            user_graph_interaction(),
                            xxl={"size": 5, "order": 3},
                            xs=12,
                            className="pt-3 border-top",
                        ),
                    ],
                    align="start",
                )
            ],
        )

    def table_C2_tab():
        return dbc.Tab(
            tab_id="table-tab",
            label=table_c2_label(config, lang),
            children=[
                Loading(html.H5(id="table-C2-title", className="mt-3")),
                Loading(html.Div(id="table-C2")),
            ],
        )

    def help_tab():
        """
        Tab for software usage documentation.
        """
        return dbc.Tab(
            tab_id="help-tab",
            label=help_tab_label(config, lang),
            children=[
                dbc.Tabs(
                    id="help_tabs",
                    children=[
                        dbc.Tab(
                            tab_id=f"help_tab-{index}",
                            label=help_subtab_label(config, lang, index),
                            children=dbc.Row(
                                dbc.Col(
                                    interpret(
                                        help_subtab_content(config, lang, index)
                                    ),
                                    xs=12, xl=6
                                )
                            ),
                            className="help_tab pt-3",
                        )
                        for index in range(len(config["help"]["tabs"][lang]))
                    ],
                    className="pt-3",
                    **config["ui"]["controls"]["help_tabs"],
                )
            ],
        )

    def about_tab():
        return dbc.Tab(
            tab_id="about-tab",
            label=about_tab_label(config, lang),
            children=dbc.Tabs(
                id="about_tabs",
                children=[
                    dbc.Tab(
                        tab_id=f"about_tab-{index}",
                        label=about_subtab_label(config, lang, index),
                        children=card_set(
                            about_subtab_card_spec(config, lang, index),
                            col_args=dict(xs=12, md=6, xxl=4, className="mb-3"),
                        ),
                        className="about_tab pt-3",
                    )
                    for index in range(len(config["about"]["tabs"][lang]))
                ],
                className="pt-3",
                **config["ui"]["controls"]["about_tabs"],
            ),
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
            ),
            dcc.Store(id="local_preferences", storage_type="local"),
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
                        children=[
                            map_tab(),
                            table_C2_tab(),
                            help_tab(),
                            about_tab(),
                        ],
                        **config["ui"]["controls"]["main_tabs"],
                    )
                ),
                style={"margin-top": "1em"},
            ),
            *internal_data(),
        ],
    )
