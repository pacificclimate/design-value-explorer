def triggered_by(name, ctx):
    """
    Return boolean indicating whether the callback was triggered by the
    Input identified by `id`.

    Note: `name` is checked by `startswith` against the triggers.
    You can specify just the id of the component, or the id and property,
    as `<id>.<prop>`. To avoid overlap with similarly named components,
    specify `<id>.` if you are just checking the id.

    :param name: name of Input dependency (optionally including property).
    :param ctx: dash.callback_context inside callback
    :return: Boolean
    """
    return any(trigger["prop_id"].startswith(name) for trigger in ctx.triggered)
