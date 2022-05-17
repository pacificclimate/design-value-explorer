import logging

import dash
from dash.dependencies import Input, Output, State
from dash import dash_table, dcc

from dve.config import (
    dv_has_climate_regime, future_change_factor_label, dv_roundto, dv_name,
    dv_units, file_exists, filepath_for, units_suffix, dv_tier, table_c2_title,
    table_c2_no_table_data_msg, table_c2_no_station_data_msg,
)
from dve.data import get_data_object
from dve.config import dv_label
from dve.math_utils import round_to_multiple
from dve.timing import timing


logger = logging.getLogger(__name__)
timing_log = logger.info


def add(app, config):
    def make_data_table(design_variable):
        historical_name_and_units = dv_label(
            config, design_variable, climate_regime="historical"
        )
        historical_units, future_units = (
            dv_units(config, design_variable, climate_regime, nice=False)
            for climate_regime in ("historical", "future")
        )
        future_dataset_ids = config["ui"]["future_change_factors"]

        title = table_c2_title(config, design_variable)

        # Show error message if configured data file does not exist.
        if not file_exists(
            filepath_for(
                config,
                design_variable,
                climate_regime="historical",
                historical_dataset_id="table",
            )
        ):
            return (
                title,
                dcc.Markdown(table_c2_no_table_data_msg(config))
            )

        historical_dataset = get_data_object(
            config, design_variable, "historical", historical_dataset_id="table"
        ).data_frame()

        nbcc_hx_value_col_id = f"{design_variable} (NBCC)"

        pcic_revised_hx_value_col_id = f"{design_variable} ({historical_units})"

        column_units_suffix = (
            f" ({future_units})" if future_units != "ratio" else " "
        )
        cf_value_col_ids = [
            f"CF_{future_dataset_id}C{column_units_suffix}"
            for future_dataset_id in future_dataset_ids
        ]

        try:
            display_dataset = historical_dataset[
                [
                    "Location",
                    "prov",
                    "Longitude",
                    "Latitude",
                    nbcc_hx_value_col_id,
                    pcic_revised_hx_value_col_id,
                    *cf_value_col_ids,
                ]
            ]
        except KeyError as e:
            return (title, f"An error occurred reading Table C2: {str(e)}")

        # Round CF values according to config
        for col_id in cf_value_col_ids:
            display_dataset[col_id] = display_dataset[col_id].apply(
                lambda x: round_to_multiple(
                    x, dv_roundto(config, design_variable, "future")
                )
            )

        column_info = {
            "Location": {"name": ["", "Location"], "type": "text"},
            "prov": {"name": ["", "Province"], "type": "text"},
            "Longitude": {"name": ["", "Longitude"], "type": "numeric"},
            "Latitude": {"name": ["", "Latitude"], "type": "numeric"},
            pcic_revised_hx_value_col_id: {
                "name": [historical_name_and_units, "PCIC"],
                "type": "numeric",
                "format": {
                    "nully": "n/a",
                },
            },
            nbcc_hx_value_col_id: {
                "name": [historical_name_and_units, "NBCC"],
                "type": "numeric",
                "format": {
                    "nully": "n/a",
                },
            },
            **{
                cf_value_col_id: {
                    "name": [
                        dv_label(
                            config, design_variable, climate_regime="future"
                        ),
                        f"CF {future_change_factor_label(config, future_dataset_id)}",
                    ],
                    "type": "numeric",
                    "format": {
                        "nully": "n/a",
                    },
                }
                for cf_value_col_id, future_dataset_id in zip(
                    cf_value_col_ids, future_dataset_ids
                )
            },
        }

        return (
            title,
            dash_table.DataTable(
                columns=[
                    {"id": id_, **column_info[id_]}
                    for id_ in display_dataset.columns
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
            ),
        )

    @app.callback(
        Output("table-C2-title", "children"),
        Output("table-C2", "children"),
        Input("main_tabs", "active_tab"),
        Input("design_variable", "value"),
    )
    def update_tablec2(main_tabs_active_tab, design_variable):
        # Do not update if the tab is not selected
        if main_tabs_active_tab != "table-tab":
            return dash.no_update

        # Show "No data" if there is no data for this variable
        if not dv_has_climate_regime(config, design_variable, "historical"):
            return (
                table_c2_no_station_data_msg(config, design_variable),
                None,
            )

        with timing(f"Table C2 for {design_variable}", timing_log):
            data_table = make_data_table(design_variable)
        return data_table
