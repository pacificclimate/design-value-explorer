import urllib.parse

import dash
from dash.dependencies import Input, Output, State


def add(app, config):
    @app.callback(
        Output("design_variable", "value"),
        Output("url", "search"),
        Input("design_variable", "value"),
        Input("url", "search"),
    )
    def update_design_variable(design_variable, url_search):
        """
        Mutual (circular) update of design variable selector value
        by url query parameter `dv`, and vice-versa.
        """
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "design_variable":
            return dash.no_update, f"?dv={design_variable}"

        qps = urllib.parse.parse_qs(url_search[1:])
        # print("### query params", qps)
        if "dv" in qps:
            dv = qps["dv"][0]
            if dv in config["values"]["ui"]["dvs"]:
                return dv, dash.no_update
        return dash.no_update, dash.no_update


