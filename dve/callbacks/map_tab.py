from dash.dependencies import Input, Output
from dve.config import map_tab_label


def add(app, config):
    @app.callback(Output("map-tab", "label"), Input("language", "value"))
    def update_about_tab_label(lang):
        return map_tab_label(config, lang)
