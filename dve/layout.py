from dash import html
import dash_bootstrap_components as dbc
from dash import dcc
import dash_daq as daq
from dve.config import (
    overlay_options_control_columns,
    color_bar_options_ctrl_width,
    map_tab_label,
    table_c2_label,
    about_tab_label,
    about_subtab_label,
    about_subtab_card_spec,
)
from dve.text_utils import interpret


def main(app, config, lang="en"):
    """
    Top-level layout component. `app.layout` should be set to what this function
    returns.
    """

    def Loading(*args, **kwargs):
        """
        Add loading config to a dcc.Loading call.
        """
        return dcc.Loading(*args, **kwargs, **config["values"]["ui"]["loading"])

    def header():
        """
        Layout element for parts common to all tabs.
        Not actually a "header" so should probably be renamed or broken up into
        true header and other parts.

        Returns a list of rows.
        """
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
                        xs=5,
                        className="align-self-center text-end",
                    ),
                    dbc.Col(
                        html.A(
                            id="app_title",
                            href=app.get_relative_path("/"),
                            style={
                                "font-size": "2em",
                                "color": "inherit",
                                "text-decoration": "none",
                            },
                        ),
                        xs=5,
                        className="align-self-center text-start",
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="language",
                            options=[
                                {"label": "English", "value": "en"},
                                {"label": "Français", "value": "fr"},
                            ],
                            value="en",
                        ),
                        xs=2,
                    ),
                ],
                className="pb-1 mb-3 border-bottom",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Label(id="dv_dropdown_label"),
                        xs=12,
                        md=3,
                        lg=2,
                        xxl=1,
                        className="align-self-center",
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="design_variable",
                            **config["values"]["ui"]["controls"][
                                "design-value-id"
                            ],
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
        return [
            # Section title
            dbc.Row(dbc.Col(html.H5(id="overlay_options_section_title"))),
            # Control titles
            dbc.Row(id="overlay_options_control_titles"),
            # Controls
            dbc.Row(
                [
                    dbc.Col(control, width=width)
                    for control, width in zip(
                        (
                            dcc.RadioItems(
                                id="climate_regime",
                                **config["values"]["ui"]["controls"][
                                    "climate-regime"
                                ],
                            ),
                            html.Div(
                                id="global_warming",
                                children=[
                                    html.Div(style={"height": "2.5em"}),
                                    dcc.Dropdown(
                                        id="future_dataset_id",
                                        **config["values"]["ui"]["controls"][
                                            "future-dataset"
                                        ],
                                    ),
                                ],
                                **config["values"]["ui"]["controls"][
                                    "global_warming"
                                ],
                            ),
                            daq.BooleanSwitch(
                                id="show_stations",
                                **config["values"]["ui"]["controls"][
                                    "stations"
                                ],
                            ),
                            daq.BooleanSwitch(
                                id="show_grid",
                                **config["values"]["ui"]["controls"]["grid"],
                            ),
                        ),
                        [
                            column["width"]
                            for column in overlay_options_control_columns(
                                config, lang
                            )
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
        colour_maps = config["values"]["map"]["colour_maps"]
        # Add reverse options, too
        cmap_r = tuple(f"{color}_r" for color in colour_maps)
        colour_maps += cmap_r

        cfg = config["text"]["labels"][lang]["colorscale-options"]

        # Controls by column key in config
        controls = {
            "color-map": dcc.Dropdown(
                id="color_map",
                **config["values"]["ui"]["controls"]["colour-map"],
            ),
            "scale": dcc.Dropdown(
                id="color_scale_type",
                **config["values"]["ui"]["controls"]["scale"],
            ),
            "num-colors": html.Div(
                daq.Slider(
                    id="num_colors",
                    **config["values"]["ui"]["controls"]["num-colours"],
                ),
                style={"padding-top": "3em"},
            ),
            "range": Loading(
                html.Div(
                    dcc.RangeSlider(
                        id="color_scale_data_range",
                        **config["values"]["ui"]["controls"]["colourbar-range"],
                    ),
                    # RangeSlider has unwanted horiz padding of 25px.
                    style={"margin": "2em -25px"},
                )
            ),
        }

        return [
            # Section title
            dbc.Row(dbc.Col(html.H5(id="colourbar_options_section_title"))),
            # Control titles
            dbc.Row(id="colourbar_options_control_titles"),
            # Controls
            dbc.Row(
                [
                    dbc.Col(
                        controls[col_key],
                        width=color_bar_options_ctrl_width(
                            config, lang, col_key
                        ),
                    )
                    for col_key in cfg["column-order"]
                ],
                style={"font-size": "0.8em"},
            ),
        ]

    def map_pointer_output():
        """
        Layout for map pointer output.
        :return: list of dbc.Row
        """
        return [
            dbc.Row(id="map_pointer_output_heading"),
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
                                    config=config["values"]["ui"]["graph"],
                                )
                            ),
                            xxl={"size": 7, "order": 3},
                            xs=12,
                            className="border-top",
                        ),
                        dbc.Col(
                            map_pointer_output(),
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
            id="help-tab",
            tab_id="help-tab",
            children=[
                dbc.Tabs(
                    id="help_tabs",
                    className="pt-3",
                    **config["values"]["ui"]["controls"]["help_tabs"],
                )
            ],
        )

    def about_tab():
        return dbc.Tab(
            id="about-tab",
            tab_id="about-tab",
            children=dbc.Tabs(
                id="about_tabs",
                className="pt-3",
                **config["values"]["ui"]["controls"]["about_tabs"],
            ),
        )

    def internal_data():
        """
        Layout components for storing/sharing data between callbacks (and
        callback invocations) on the client side, using a hidden div (ick!). See
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
                        **config["values"]["ui"]["controls"]["main_tabs"],
                    )
                ),
                style={"margin-top": "1em"},
            ),
            *internal_data(),
        ],
    )
