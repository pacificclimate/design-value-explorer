import yaml
from dve.data import load_data
from dve.app import get_app


print("\n\n### Running app")

print(f"### Loading configuration")
with open("config.yml", "r") as ymlfile:
    config = yaml.load(ymlfile)
print(f"### Config loaded. {config}")

print("### Calling load_data")
data = load_data(config)
print("### Data loaded")

app = get_app(config, data)

if __name__ == "__main__":
    print("### Running app")
    app.run_server(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
