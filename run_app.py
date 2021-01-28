import yaml
from dve.data import load_data
from dve.app import get_app

from frozendict import frozendict


# TODO: Put this somewhere else
def freeze(obj):
    """Recursively freeze the objects in obj"""
    if type(obj) == dict:
        return frozendict((key, freeze(value)) for key, value in obj.items())
    if type(obj) == list:
        return tuple(freeze(value) for value in obj)
    return obj


print("\n\n### Running app")

print(f"### Loading configuration")
with open("config.yml", "r") as ymlfile:
    config = freeze(yaml.load(ymlfile))
print(f"### Config loaded. {config}")

print("### Calling load_data")
data = load_data(config)
print("### Data loaded")

app = get_app(config, data)
# app.run_server(host='0.0.0.0', debug=True)
