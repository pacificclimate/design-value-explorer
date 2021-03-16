import csv
import os.path

from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_bootstrap_components as dbc

from dve.data import get_data
from dve.download_utils import (
    download_filename,
    download_filepath,
    download_url,
)
from dve.map_utils import (
    pointer_rlonlat,
    rlonlat_to_rindices,
    pointer_rindices,
    rindices_to_lonlat,
    pointer_value,
)


def add(app, config):

    # TODO: Extract these?
    def value_table(*items):
        return dbc.Table(
            [
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Th(name, style={"width": "5em"}),
                                html.Td(value),
                            ]
                        )
                        for name, value in items
                    ]
                )
            ],
            bordered=True,
            size="sm",
        )

    def dv_value(
        design_value_id,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
        rlon,
        rlat,
    ):
        data = get_data(
            config,
            design_value_id,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        (dv_var_name,) = data.data_vars
        ix, iy = rlonlat_to_rindices(data, rlon, rlat)
        return data[dv_var_name].values[iy, ix]

    def dv_table(rlon, rlat, selected_dv=None, selected_interp=None):
        """
        Return a table listing values of design values at a location specified
        by rotated coordinates rlon, rlat

        :param rlon:
        :param rlat:
        :return:
        """
        return dbc.Table(
            [
                html.Thead(
                    [
                        html.Tr(
                            [
                                html.Th("DV"),
                                html.Th("Model"),
                                html.Th("Reconstruction"),
                            ]
                        )
                    ]
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [html.Th(design_value_id, style={"width": "5em"})]
                            + [
                                html.Td(
                                    round(
                                        float(
                                            dv_value(
                                                design_value_id,
                                                "historical",
                                                dataset_id,
                                                rlon,
                                                rlat,
                                            )
                                        ),
                                        3,
                                    ),
                                    style={
                                        "color": "red"
                                        if design_value_id == selected_dv
                                        and dataset_id == selected_interp
                                        else "inherit"
                                    },
                                )
                                for dataset_id in ("model", "reconstruction")
                            ]
                        )
                        for design_value_id in config["dvs"].keys()
                    ]
                ),
            ],
            bordered=True,
            size="sm",
        )

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
        design_value_id_ctrl,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        # TODO: Can we use a fixed value ("model" or "reconstruction") instead
        #  of interpolation_ctrl? Note: Each type of dataset has a different
        #  lat-lon grid.

        # TODO: DRY this up with respect to display_click_info when we have
        #   settled interface.

        if hover_data is None:
            return None

        dataset = get_data(
            config,
            design_value_id_ctrl,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        rlon, rlat = pointer_rlonlat(hover_data)
        ix, iy = pointer_rindices(hover_data, dataset)
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(hover_data)

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            ),
            # dv_table(
            #     rlon,
            #     rlat,
            #     selected_dv=design_value_id_ctrl,
            #     selected_interp=interpolation_ctrl,
            # ),
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
        design_value_id_ctrl,
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

        dataset = get_data(
            config,
            design_value_id_ctrl,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        return [
            html.A(
                "Download this data",
                href=download_url(lon, lat),
                download=download_filename(lon, lat),
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
        design_value_id_ctrl,
        climate_regime,
        historical_dataset_id,
        future_dataset_id,
    ):
        """
        To get the layout we want, we have to break the map-click callback into
        two parts: Download button and data display. Unfortunately this is
        repetitive but no other solution is known.
        """
        # TODO: Can we use a fixed value ("model" or "reconstruction" instead
        #  of interp_ctrl? ... The grids for each are different and
        #  give different values for lat/lon at the same pointer locn.
        # TODO: DRY
        if click_data is None:
            return None

        dataset = get_data(
            config,
            design_value_id_ctrl,
            climate_regime,
            historical_dataset_id,
            future_dataset_id,
        )
        rlon, rlat = pointer_rlonlat(click_data)
        ix, iy = pointer_rindices(click_data, dataset)
        # Note that lon, lat is derived from selected dataset, which may have
        # a different (coarser, finer) grid than the other datasets.
        lon, lat = rindices_to_lonlat(dataset, ix, iy)
        z, source = pointer_value(click_data)

        # Create data table for download
        with open(os.path.join("/", download_filepath(lon, lat)), "w") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(("Latitude", lat))
            writer.writerow(("Longitude", lon))
            writer.writerow(tuple())
            writer.writerow(
                ("Design Value ID", "Model Value", "Reconstruction Value")
            )
            for dv_id in config["dvs"].keys():
                writer.writerow(
                    (
                        dv_id,
                        float(
                            dv_value(dv_id, "historical", "model", rlon, rlat)
                        ),
                        float(
                            dv_value(
                                dv_id,
                                "historical",
                                "reconstruction",
                                rlon,
                                rlat,
                            )
                        ),
                    )
                )

        return [
            value_table(
                ("Lat", round(lat, 6)),
                ("Lon", round(lon, 6)),
                # (f"Z ({design_value_id_ctrl}) ({source})", round(z, 6)),
            ),
            dv_table(
                rlon,
                rlat,
                selected_dv=design_value_id_ctrl,
                selected_interp=historical_dataset_id,
            ),
        ]
