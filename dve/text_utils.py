import os
from dash import dcc, html
import dash_bootstrap_components as dbc


def interpret(source):
    os.environ["DVE_VERSION_TAG_ONLY"] = os.environ["DVE_VERSION"].split()[0]
    return dcc.Markdown(
        source.format(**os.environ), dangerously_allow_html=True
    )


def compact(iterable):
    return list(filter(None, iterable))


def card_item(card):
    color = card.get("color")
    title = card.get("title")
    header = card.get("header")
    body = card.get("body")
    return dbc.Card(
        className="me-3 mb-3 float-start",
        style={"width": "30%"},
        color=color,
        children=compact(
            (
                header and dbc.CardHeader(interpret(header)),
                title and html.H4(interpret(title), className="card-title"),
                body and dbc.CardBody(interpret(body)),
            )
        ),
    )


def card_set(cards, row_args=None, col_args=None):
    if row_args is None:
        row_args = {}
    if col_args is None:
        col_args = {}
    return dbc.Row(dbc.Col([card_item(card) for card in cards]), **row_args)
    return dbc.Row(
        [dbc.Col(card_item(card), **col_args) for card in cards], **row_args
    )
