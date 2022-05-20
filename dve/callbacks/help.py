from dash.dependencies import Input, Output
from dve.config import help_tab_label, help_subtabs


def add(app, config):
    @app.callback(Output("help-tab", "label"), Input("language", "value"))
    def update_help_tab_label(lang):
        return help_tab_label(config, lang)

    @app.callback(Output("help_tabs", "children"), Input("language", "value"))
    def update_help_subtabs(lang):
        return help_subtabs(config, lang)
