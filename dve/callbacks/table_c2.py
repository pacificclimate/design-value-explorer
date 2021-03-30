import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table

import pandas

from climpyrical.gridding import transform_coords

from dve.config import dv_has_climate_regime, future_change_factor_label
from dve.data import get_data
from dve.config import dv_label
from dve.math_utils import round_to_multiple


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        [Output("table-C2-title", "children"), Output("table-C2", "children")],
        [Input("design-value-id-ctrl", "value")],
    )
    def update_tablec2(design_value_id):
        if not dv_has_climate_regime(config, design_value_id, "historical"):
            return (
                config["ui"]["labels"]["table_C2"]["no_station_data"].format(
                    design_value_id
                ),
                None,
            )

        name_and_units = dv_label(
            config, design_value_id, climate_regime="historical"
        )

        title = config["ui"]["labels"]["table_C2"]["title"].format(
            name_and_units
        )

        historical_dataset = get_data(
            config, design_value_id, "historical", historical_dataset_id="table"
        ).data_frame()

        display_dataset = historical_dataset[
            ["Location", "Prov", "lon", "lat", "NBCC 2015", "PCIC"]
        ]
        display_dataset["PCIC"] = display_dataset["PCIC"].apply(
            lambda x: round_to_multiple(
                x, config["dvs"][design_value_id]["roundto"]
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
                design_value_id,
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
                        config["dvs"][design_value_id]["ratio_roundto"],
                    ),
                    zip(rlons, rlats),
                )
            )

            column_info[column_id] = {
                "name": [
                    dv_label(
                        config, design_value_id, climate_regime="future"
                    ),
                    f"CF ({future_change_factor_label(config, future_dataset_id)})",
                ],
                "type": "numeric",
            }

        return [
            title,
            dash_table.DataTable(
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
            ),
        ]
