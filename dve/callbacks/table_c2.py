import logging

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
from flask_caching import Cache

import pandas

from climpyrical.gridding import transform_coords

from dve.config import (
    dv_has_climate_regime, future_change_factor_label, dv_roundto,
)
from dve.data import get_data
from dve.config import dv_label
from dve.math_utils import round_to_multiple
from dve.timing import timing


logger = logging.getLogger("dve")
timing_log = logger.info


def add(app, config):
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'table-c2-cache'
    })

    @cache.memoize(timeout=config["table_C2"]["cache_timeout"])
    def make_data_table(design_variable):
        logger.info(f"Table C2 cache miss: {design_variable}")

        name_and_units = dv_label(
            config, design_variable, climate_regime="historical"
        )

        title = config["ui"]["labels"]["table_C2"]["title"].format(
            name_and_units
        )

        historical_dataset = get_data(
            config, design_variable, "historical", historical_dataset_id="table"
        ).data_frame()

        display_dataset = historical_dataset[
            ["Location", "Prov", "lon", "lat", "NBCC 2015", "PCIC"]
        ]
        display_dataset["PCIC"] = display_dataset["PCIC"].apply(
            lambda x: round_to_multiple(
                x, config["dvs"][design_variable]["roundto"]
            )
        )

        column_info = {
            "Location": {"name": ["", "Location"], "type": "text"},
            "Prov": {"name": ["", "Province"], "type": "text"},
            "lon": {"name": ["", "Longitude"], "type": "numeric"},
            "lat": {"name": ["", "Latitude"], "type": "numeric"},
            "PCIC": {"name": [name_and_units, "PCIC"], "type": "numeric"},
            "NBCC 2015": {
                "name": [name_and_units, "NBCC 2015"],
                "type": "numeric",
            },
        }

        for future_dataset_id in config["ui"]["future_change_factors"]:
            future_dataset = get_data(
                config,
                design_variable,
                "future",
                future_dataset_id=future_dataset_id,
            )
            rlons, rlats = transform_coords(
                display_dataset["lon"].values, display_dataset["lat"].values
            )
            column_id = f"CF{future_dataset_id}"
            display_dataset[column_id] = pandas.Series(
                data=map(
                    lambda coords: round_to_multiple(
                        future_dataset.data_at_rlonlat(*coords)[2],
                        dv_roundto(config, design_variable, "future"),
                    ),
                    zip(rlons, rlats),
                )
            )

            column_info[column_id] = {
                "name": [
                    dv_label(config, design_variable, climate_regime="future"),
                    f"CF ({future_change_factor_label(config, future_dataset_id)})",
                ],
                "type": "numeric",
            }

        return title, dash_table.DataTable(
            columns=[
                {"id": id, **column_info[id]}
                for id in display_dataset.columns
            ],
            style_table={
                # "width": "100%",
                # 'overflowX': 'auto',
            },
            style_cell={
                "textAlign": "center",
                "whiteSpace": "normal",
                "height": "auto",
                "padding": "5px",
                "width": "2em",
                "minWidth": "2em",
                "maxWidth": "2em",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "Location"},
                    "width": "5em",
                    "textAlign": "left",
                }
            ],
            style_as_list_view=True,
            style_header={"backgroundColor": "white", "fontWeight": "bold"},
            page_action="none",
            filter_action="native",
            data=display_dataset.to_dict("records"),
            export_format="csv",
        )


    @app.callback(
        [Output("table-C2-title", "children"), Output("table-C2", "children")],
        [Input("main_tabs", "active_tab"), Input("design_variable", "value")],
    )
    def update_tablec2(main_tabs_active_tab, design_variable):
        # Do not update if the tab is not selected
        if main_tabs_active_tab != "table-tab":
            raise PreventUpdate

        # Show "No data" if there is no data for this variable
        if not dv_has_climate_regime(config, design_variable, "historical"):
            return (
                config["ui"]["labels"]["table_C2"]["no_station_data"].format(
                    design_variable
                ),
                None,
            )

        with timing(f"Table C2 for {design_variable}", timing_log):
            data_table = make_data_table(design_variable)
        return data_table
