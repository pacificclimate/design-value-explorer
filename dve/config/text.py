import logging
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from dve.config.values import units_suffix, dv_units, nice_units, dv_tier
from dve.text_utils import interpret, card_set

logger = logging.getLogger(__name__)


def dv_name(config, lang, design_variable):
    """
    Return the name of a design variable. Currently, this is the internal
    id of the DV, so `config` and `lang` are not used.
    That could conceivably change.
    """
    return design_variable


def dv_label(
    config,
    lang,
    design_variable,
    climate_regime="historical",
    with_units=True,
    with_description=False,
):
    """
    Return the name, with optional description, and units of a DV.
    """
    description = (
        f" {config['text']['labels'][lang]['dvs'][design_variable]['description']}"
        if with_description
        else ""
    )
    units = (
        units_suffix(dv_units(config, design_variable, climate_regime))
        if with_units
        else ""
    )
    return f"{dv_name(config, lang, design_variable)}{description}{units}"


def app_title(config, lang):
    return config["text"]["labels"][lang]["app_title"]


def dv_dropdown_label(config, lang):
    return config["text"]["labels"][lang]["dv_dropdown"]


def dv_dropdown_options(config, lang):
    return [
        {
            "label": dv_label(
                config,
                lang,
                design_variable,
                with_units=False,
                with_description=True,
            ),
            "value": design_variable,
        }
        for design_variable in config["values"]["ui"]["dvs"]
    ]


def future_dataset_ctrl_options(config, lang):
    return [
        {
            "label": future_change_factor_label(
                config, lang, dataset_id, which="long"
            ),
            "value": dataset_id,
        }
        for dataset_id in config["values"]["ui"]["future_change_factors"]
    ]


def climate_regime_label(config, lang, climate_regime, which="long"):
    return config["text"]["labels"][lang]["climate_regime"][climate_regime][
        which
    ]


def historical_dataset_label(config, lang, dataset_id):
    return config["text"]["labels"][lang]["historical_dataset"][dataset_id]


def interpolation_value_label(config, lang):
    return config["text"]["labels"][lang]["interpolation"]


def future_change_factor_label(
    config, lang, dataset_id, which="short", nice=True
):
    units, separator = nice_units(config, "degC") if nice else ("degC", " ")
    return config["text"]["labels"][lang]["future_change_factors"][
        which
    ].format(value=dataset_id, separator=separator, units=units)


def download_table_headers(
    config, lang, climate_regime, dataset_ids, nice=True
):
    if climate_regime == "historical":
        value_headers = (interpolation_value_label(config, lang),)
    else:
        value_headers = tuple(
            future_change_factor_label(config, lang, dataset_id, nice=nice)
            for dataset_id in dataset_ids
        )
    return (
        tuple(
            download_table_label(config, lang, column)
            for column in ("dv", "units")
        )
        + value_headers
    )


def download_table_label(config, lang, column):
    return config["text"]["labels"][lang]["download_table"][column]


def dataset_label(
    config,
    lang,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
    which="short",
    nice=True,
):
    if climate_regime == "historical":
        return historical_dataset_label(config, lang, historical_dataset_id)
    return future_change_factor_label(
        config, lang, future_dataset_id, which=which, nice=nice
    )


def map_title(
    config,
    lang,
    design_variable,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
):
    dl = dataset_label(
        config,
        lang,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        which="short",
        nice=True,
    )
    dataset = "" if climate_regime == "historical" else f" ({dl})"
    return config["text"]["labels"][lang]["map"]["title"][
        climate_regime
    ].format(
        dv=dv_label(
            config, lang, design_variable, climate_regime, with_description=True
        ),
        tier=dv_tier(config, design_variable),
        climate_regime=climate_regime_label(
            config, lang, climate_regime, which="short"
        ),
        dataset=dataset,
    )


def climate_regime_ctrl_options(config, lang, which="long"):
    return [
        {
            "label": config["text"]["labels"][lang]["climate_regime"][cr][
                which
            ],
            "value": cr,
        }
        for cr in ("historical", "future")
    ]


def overlay_options_section_title(config, lang):
    return config["text"]["labels"][lang]["overlay-options"]["title"]


def overlay_options_control_titles(config, lang):
    return [
        dbc.Col(html.Label(column["title"]), width=column["width"])
        for column in overlay_options_control_columns(config, lang)
    ]


def overlay_options_control_columns(config, lang):
    return config["text"]["labels"][lang]["overlay-options"]["columns"]


def show_stations_label(config, lang):
    return {
        **config["values"]["ui"]["controls"]["stations"]["label"],
        "label": config["text"]["labels"][lang]["show_stations"]["label"],
    }


def color_map_ctrl_options(config, lang=None):
    # At present this is language-independent
    return [
        {"value": x, "label": x} for x in config["values"]["map"]["colour_maps"]
    ]


def scale_ctrl_options(config, lang):
    return config["text"]["labels"][lang]["color_scale_type"]


def colourbar_options_section_title(config, lang):
    return config["text"]["labels"][lang]["colorscale-options"]["title"]


def color_bar_options_ctrl_title(config, lang, col_key):
    return (
        config["text"]["labels"][lang]["colorscale-options"]["columns"][
            col_key
        ]["title"],
    )


def colourbar_options_control_titles(config, lang):
    cfg = config["text"]["labels"][lang]["colorscale-options"]
    return [
        dbc.Col(
            html.Label(
                color_bar_options_ctrl_title(config, lang, col_key),
                id=f"colorscale_options_label_{col_key}",
            ),
            width=color_bar_options_ctrl_width(config, lang, col_key),
        )
        for col_key in cfg["column-order"]
    ]


def color_bar_options_ctrl_width(config, lang, col_key):
    return (
        config["text"]["labels"][lang]["colorscale-options"]["columns"][
            col_key
        ]["width"],
    )


def colorscale_options_label_range(config, lang, min=None, max=None):
    return config["text"]["labels"][lang]["colorscale_options_range"][
        "label"
    ].format(min=min, max=max)


def map_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["map-tab"]


def table_c2_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["table-tab"]


def help_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["help-tab"]


def help_subtab_label(config, lang, index):
    return config["text"]["help"]["tabs"][lang][index]["label"]


def help_subtab_content(config, lang, index):
    return config["text"]["help"]["tabs"][lang][index]["content"]


def about_tab_label(config, lang):
    return config["text"]["labels"][lang]["main_tabs"]["about-tab"]


def about_subtab_label(config, lang, index):
    return config["text"]["about"]["tabs"][lang][index]["label"]


def about_subtab_card_spec(config, lang, index):
    # TODO: This will need some extra effort for multilang
    return config["text"]["about"]["tabs"][lang][index]["cards"]


def table_c2_title(config, lang, design_variable):
    return config["text"]["labels"][lang]["table_C2"]["title"].format(
        name=dv_name(config, lang, design_variable),
        tier=dv_tier(config, design_variable),
        name_and_units=dv_label(
            config, lang, design_variable, climate_regime="historical"
        ),
    )


def table_c2_no_table_data_msg(config, lang):
    return config["text"]["labels"][lang]["table_C2"]["no_table_data_error"]


def table_c2_no_station_data_msg(config, lang, design_variable):
    return config["text"]["labels"][lang]["table_C2"]["no_station_data"].format(
        design_variable
    )


def location_label(config, lang, which="long"):
    return config["text"]["labels"][lang]["misc"]["location"][which]


def province_label(config, lang, which="long"):
    return config["text"]["labels"][lang]["misc"]["province"][which]


def longitude_label(config, lang, which="long"):
    return config["text"]["labels"][lang]["misc"]["longitude"][which]


def latitude_label(config, lang, which="long"):
    return config["text"]["labels"][lang]["misc"]["latitude"][which]


def download_data_button_text(config, lang):
    return config["text"]["labels"][lang]["misc"]["download_data_button_text"]


def map_pointer_output_heading(config, lang):
    cfg = config["text"]["labels"][lang]["map_pointer_output"]
    return dbc.Col(
        [
            html.H5(cfg["title"]),
            dcc.Markdown(cfg["subtitle"], style={"font-size": "0.8em"}),
        ]
    )


def map_no_dvs_for_climate_regime_msg(
    config, lang, climate_regime, design_variable
):
    # TODO: In French, this message is grammatically slightly wrong because
    #  the gender of the adjective "futur" does not accord with the noun
    #  it modifies in the message. Argh.
    return config["text"]["labels"][lang]["map"][
        "no_dvs_for_climate_regime"
    ].format(
        what=climate_regime_label(
            config, lang, climate_regime, which="short"
        ).lower(),
        dv=dv_name(config, lang, design_variable),
    )


def map_no_data_error(
    config,
    lang,
    design_variable,
    climate_regime,
    historical_dataset_id,
    future_dataset_id,
):
    return config["text"]["labels"][lang]["map"]["no_data_error"].format(
        title=map_title(
            config,
            lang,
            design_variable,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
    )


def map_heatmap_hover_template(config, lang, design_variable, climate_regime):
    return config["text"]["labels"][lang]["map"]["heatmap_hover_template"].format(
        dv_label=dv_label(config, lang, design_variable, climate_regime)
    )


def map_station_hover_template(config, lang, design_variable, climate_regime):
    return config["text"]["labels"][lang]["map"]["station_hover_template"].format(
        dv_label=dv_label(config, lang, design_variable, climate_regime)
    )


def help_subtabs(config, lang):
    return [
        dbc.Tab(
            tab_id=f"help_tab-{index}",
            label=help_subtab_label(config, lang, index),
            children=dbc.Row(
                dbc.Col(
                    interpret(help_subtab_content(config, lang, index)),
                    xs=12,
                    xl=6,
                )
            ),
            className="help_tab pt-3",
        )
        for index in range(len(config["text"]["help"]["tabs"][lang]))
    ]


def about_subtabs(config, lang):
    return [
        dbc.Tab(
            tab_id=f"about_tab-{index}",
            label=about_subtab_label(config, lang, index),
            children=card_set(
                about_subtab_card_spec(config, lang, index),
                col_args=dict(xs=12, md=6, xxl=4, className="mb-3"),
            ),
            className="about_tab pt-3",
        )
        for index in range(len(config["text"]["about"]["tabs"][lang]))
    ]
