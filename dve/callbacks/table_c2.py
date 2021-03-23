import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table

from dve.config import dv_has_climate_regime
from dve.data import get_data
from dve.labelling_utils import dv_label


logger = logging.getLogger("dve")


def add(app, config):
    @app.callback(
        [Output("table-C2-dv", "children"), Output("table", "children")],
        [Input("design-value-id-ctrl", "value")]
    )
    def update_tablec2(design_value_id):
        if not dv_has_climate_regime(config, design_value_id, "historical"):
            raise PreventUpdate

        name_and_units = dv_label(
            config, design_value_id, climate_regime="historical"
        )
        df = get_data(
            config,
            design_value_id,
            "historical",
            historical_dataset_id="table"
        ).data_frame()
        df = (
            df[["Location", "Prov", "lon", "lat", "PCIC", "NBCC 2015"]]
                .round(3)
        )

        column_info = {
            "Location": {"name": ["", "Location"], "type": "text"},
            "Prov": {"name": ["", "Province"], "type": "text"},
            "lon": {"name": ["", "Longitude"], "type": "numeric"},
            "lat": {"name": ["", "Latitude"], "type": "numeric"},
            "PCIC": {"name": [name_and_units, "PCIC"], "type": "numeric"},
            "NBCC 2015": {
                "name": [name_and_units, "NBCC 2015"],
                "type": "numeric"
            },
        }

        return [
            name_and_units,
            dash_table.DataTable(
                columns=[{"id": id, **column_info[id]} for id in df.columns],
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
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Location"},
                        "width": "5em",
                        "textAlign": "left",
                    },
                ],
                style_as_list_view=True,
                style_header={"backgroundColor": "white", "fontWeight": "bold"},
                page_action="none",
                filter_action="native",
                data=df.to_dict("records"),
            )
        ]
