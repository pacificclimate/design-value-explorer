import logging
import functools

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_bootstrap_components as dbc

from dve.config import dv_has_climate_regime
from dve.data import get_data, dv_value
from dve.download_utils import (
    download_filename,
    download_url,
    get_download_data,
    create_download_file,
)
from dve.labelling_utils import (
    dv_name,
    dv_units,
    dv_label,
    climate_regime_label,
)
from dve.map_utils import (
    pointer_rlonlat,
    pointer_rindices,
    rlonlat_to_rindices,
    rindices_to_lonlat,
    pointer_value,
)


logger = logging.getLogger("dve")


# TODO: Place somewhere else (layout.components)?
def map_pointer_table(
    config,
    climate_regime,
    design_value_ids, dataset_ids, data_values,
    selected_dv=None,
    selected_dataset_id=None,
):
    """
    Return a table listing values of design values at a location specified
    by rotated coordinates rlon, rlat
    """
    if climate_regime == "historical":
        value_headers = tuple(
            f"{dataset_id.capitalize()} value" for dataset_id in dataset_ids
        )
    else:
        value_headers = dataset_ids

    logger.debug(
        f"""map_pointer_table (
            climate_regime={climate_regime},
            selected_dv={selected_dv},
            selected_dataset_id={selected_dataset_id},
        )
        """
    )

    return dbc.Table(
        [
            html.Caption(
                climate_regime_label(config, climate_regime),
                style={"caption-side": "top", "padding": "0 0 0.5em 0"}
            ),
            html.Thead(
                html.Tr(
                    [html.Th(hdg) for hdg in ("DV", "Units") + value_headers]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Th(dv_name(config, design_value_id)),
                            html.Th(
                                dv_units(
                                    config, design_value_id, climate_regime
                                ),
                                style={"width": "5em"},
                            ),
                        ]
                        + [
                            html.Td(
                                round(data_value, 3),
                                style={
                                    "color": "red"
                                    if design_value_id == selected_dv
                                    and dataset_id == selected_dataset_id
                                    else "inherit"
                                },
                            )
                            for dataset_id, data_value in zip(dataset_ids, data_row)
                        ]
                    )
                    for design_value_id, data_row in zip(design_value_ids, data_values)
                ]
            ),
        ],
        bordered=True,
        size="sm",
    )


def value_table(*items):
    return dbc.Table(
        [
            html.Tbody(
                [
                    html.Tr(
                        [html.Th(name, style={"width": "5em"}), html.Td(value)]
                    )
                    for name, value in items
                ]
            )
        ],
        bordered=True,
        size="sm",
    )


def add(app, config):
    @functools.lru_cache(maxsize=10)
    def download_info(
        rlon,
        rlat,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        logger.debug("download_info: get_data")
        dataset = get_data(
            config,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        ix, iy = rlonlat_to_rindices(dataset, rlon, rlat)
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        url = download_url(lon, lat, climate_regime)
        filename = download_filename(lon, lat, climate_regime)
        return lon, lat, url, filename


    @app.callback(
        Output("hover-info", "children"),
        [
            Input("my-graph", "hoverData"),
            Input("design-value-id-ctrl", "value"),
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
        ],
    )
    def display_hover_info(
        hover_data,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        if hover_data is None:
            return None

        if not dv_has_climate_regime(
            config, design_value_id, climate_regime
        ):
            raise PreventUpdate

        rlon, rlat = pointer_rlonlat(hover_data)

        # logger.debug("display_hover_info: get_data")
        # dataset = get_data(
        #     config,
        #     design_value_id,
        #     climate_regime,
        #     historical_dataset_id,
        #     future_dataset_id,
        # )
        # ix, iy = pointer_rindices(hover_data, dataset)
        # lon, lat = rindices_to_lonlat(dataset, ix, iy)
        # z, source = pointer_value(hover_data)

        lon, lat, *unused = download_info(
            rlon,
            rlat,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            )
        ]

    # TODO: This can be better done by setting the "href" and "download"
    #   properties on a static download link established in layout.py.
    @app.callback(
        Output("data-download-header", "children"),
        [
            Input("my-graph", "clickData"),
            Input("design-value-id-ctrl", "value"),
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
        ],
    )
    def display_download_button(
        click_data,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        """
        To get the layout we want, we have to break the map-click callback into
        two parts: Download button and data display. Unfortunately this is
        repetitive but no other solution is known.
        """
        logger.debug(
            f"""display_download_button(
                click_data={click_data},
                design_value_id={design_value_id},
                climate_regime={climate_regime},
                historical_dataset_id={historical_dataset_id},
                future_dataset_id={future_dataset_id},
            )"""
        )

        if click_data is None:
            return None

        if not dv_has_climate_regime(
            config, design_value_id, climate_regime
        ):
            raise PreventUpdate

        rlon, rlat = pointer_rlonlat(click_data)

        # logger.debug("display_download_button: get_data")
        # dataset = get_data(
        #     config,
        #     design_value_id,
        #     climate_regime,
        #     historical_dataset_id,
        #     future_dataset_id,
        # )
        # ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        # lon, lat = rindices_to_lonlat(dataset, ix, iy)
        # z, source = pointer_value(click_data)

        lon, lat, url, filename = download_info(
            rlon,
            rlat,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        
        return [
            html.A(
                "Download this data",
                href=url,
                download=filename,
                className="btn btn-primary btn-sm mb-1",
            )
        ]

    @app.callback(
        Output("click-info", "children"),
        [
            Input("my-graph", "clickData"),
            Input("design-value-id-ctrl", "value"),
            Input("climate-regime-ctrl", "value"),
            Input("historical-dataset-ctrl", "value"),
            Input("future-dataset-ctrl", "value"),
        ],
    )
    def display_click_info(
        click_data,
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        """
        To get the layout we want, we have to break the map-click callback into
        two parts: Download button and data display. Unfortunately this is
        repetitive but no other solution is known.
        """
        if click_data is None:
            return None

        if not dv_has_climate_regime(
            config, design_value_id, climate_regime
        ):
            raise PreventUpdate

        rlon, rlat = pointer_rlonlat(click_data)

        # logger.debug("display_click_info: get_data")
        # dataset = get_data(
        #     config,
        #     design_value_id,
        #     climate_regime,
        #     historical_dataset_id,
        #     future_dataset_id,
        # )
        # ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        # lon, lat = rindices_to_lonlat(dataset, ix, iy)
        # z, source = pointer_value(click_data)

        lon, lat, url, filename = download_info(
            rlon,
            rlat,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        download_data = get_download_data(
            rlon,
            rlat,
            config,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )

        # Create data file for download
        create_download_file(lon, lat, config, climate_regime, *download_data)

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            ),
            map_pointer_table(
                config,
                climate_regime,
                *download_data,
                selected_dv=design_value_id,
                selected_dataset_id=historical_dataset_id,
            ),
        ]
