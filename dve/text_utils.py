import os
from dash import dcc


def interpret(source):
    os.environ["DVE_VERSION_TAG_ONLY"] = os.environ["DVE_VERSION"].split()[0]
    return dcc.Markdown(
        source.format(**os.environ), dangerously_allow_html=True
    )
