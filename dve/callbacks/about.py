from dash.dependencies import Input, Output
from dve.config.text import about_tab_label, about_subtabs


def add(app, config):
    @app.callback(Output("about-tab", "label"), Input("language", "value"))
    def update_about_tab_label(lang):
        return about_tab_label(config, lang)

    @app.callback(Output("about_tabs", "children"), Input("language", "value"))
    def update_about_subtabs(lang):
        return about_subtabs(config, lang)
