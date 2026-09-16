# Load Arena

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![CI](https://github.com/arash7444/load-arena/actions/workflows/CI-pipeline.yml/badge.svg)
![Status](https://img.shields.io/badge/status-active--development-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Load Arena is a Python toolkit for post-processing and comparing wind-turbine
aeroelastic simulation results. It is currently centered on HAWC2 data and
common ultimate- and fatigue-load workflows.

## Main capabilities

- Read HAWC2 results and convert them to Pandas, Xarray, or Scipp containers.
- Calculate per-simulation and load-case-family statistics.
- Calculate Ultimate Limit State (ULS) results with governing-source provenance.
- Perform rainflow counting and Damage Equivalent Load (DEL) calculations.
- Calculate Fatigue Limit State (FLS) results for complete campaigns.
- Explore statistics, family averages, fatigue results, and rainflow results
  with Plotly.

## Installation

Load Arena requires Python 3.10 or newer and uses
[uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/arash7444/load-arena.git
cd load-arena
uv sync --locked
```

The Google GenAI dependency used by the experimental AI scripts is excluded from
the default installation. Install it with:

```bash
uv sync --locked --extra ai
```

## Quick start

```python
from load_arena import LoadArenaProject

project = LoadArenaProject.from_yaml("demo/project/project.yaml")
statistics = project.run_statistics()
uls = project.run_uls()
fls = project.run_fls()

figure = statistics.explore(
    channel="Aerot._[kW]",
    statistic="max",
    x_channel="WSPgl._[m/s]",
    x_statistic="mean",
    show=False,
)
figure.show()
```

Run the comprehensive capability demo from the repository root:

```bash
uv run python demo/project/demo_load_arena.py
```

The demo configuration and load factors are illustrative, not a validated
engineering campaign.

## Documentation

- [Documentation index](docs/README.md)
- [Project configuration and workflows](docs/project_configuration.md)
- [Accessing statistics, ULS, and FLS results](docs/results_access.md)
- [Dependency audit](docs/dependency_audit.md)

## Project structure

```text
src/load_arena/       Package source
demo/project/         Comprehensive project-based example
demo/                 Focused reader example
demo/obsolete_demos/  Archived historical examples
tests/                Pytest suite and simulation fixtures
docs/                 User guides, design notes, and feature records
```

## Development status

Load Arena is under active development. Changes should preserve the documented
scientific behavior, keep full source paths in result metadata, and display only
filename basenames in user-facing Plotly labels and hover text.

Run the test suite with:

```bash
uv run pytest
```

## License

[MIT](LICENSE)
