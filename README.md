# Digital Twin

An implementation of a digital twin of a traffic management system.

## Usage

Before running this script, ensure the [world state server](https://github.com/j-leeming-uni/scc.300-world_state) is running.

```sh
poetry install
poetry shell
python3 digital_twin config.toml [MAX_ITERATIONS] [-j JUNCTION_ID]
```

A junction ID should be specified, either in the `config.toml` file, or by using passing it with `-j <ID>`.

Optionally, a maximum number of iterations can be specified.

