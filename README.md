# load-arena

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![CI](https://github.com/arash7444/load-arena/actions/workflows/CI-pipeline.yml/badge.svg)
![Status](https://img.shields.io/badge/status-active--development-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Load Arena** is a Python toolkit for post-processing and comparing wind turbine aeroelastic simulation results.

The project is mainly developed around **HAWC2** simulation results and common wind turbine load-analysis workflows.

The goal is to build reusable tools for reading simulation results, calculating load statistics, fatigue and ultimate loads, and comparing groups of simulations.


## Main Features

Load Arena currently includes:

- Reading HAWC2 result files and channel information
- Conversion of simulation data to Pandas, Xarray and Scipp data structures
- Basic statistics such as mean, standard deviation, minimum and maximum
- Grouping and averaging simulation results by load-case family
- Ultimate Limit State (ULS) load processing
- Rainflow cycle counting
- Damage Equivalent Load (DEL) calculation
- Fatigue-load processing
- Visualization of fatigue and rainflow results
- Experimental LLM integration using structured outputs and tool calling

## Project Structure

```text
load-arena/
│
├── src/load_arena/
│   ├── data_reader/      # HAWC2 data reading and data conversion
│   ├── case_loader/      # Load-case configuration and input handling
│   ├── process/          # Statistics, ULS, rainflow and DEL calculations
│   ├── visualization/    # Result visualization
│   ├── AI/               # Experimental LLM/tool-calling integration
│   └── utils/            # Utility functions
│
├── demo/                 # Example scripts
├── tests/                # Pytest test suite
├── docs/                 # Design notes and feature specifications
└── pyproject.toml
```

## Installation

The project uses `uv` for dependency and environment management.

```bash
git clone https://github.com/arash7444/load-arena.git
cd load-arena

uv sync
```

Run the tests with:

```bash
uv run pytest
```

## Example Workflows

The `demo` directory contains example scripts for workflows such as:

- statistics calculation
- family averaging
- ULS calculation
- rainflow counting
- DEL calculation

For example:

```bash
uv run python demo/call_fatigue_rainflow.py
```


## Project-based Python API

One project represents a turbine/model analysis campaign. YAML coordinates the
campaign; individual ULS/FLS cases and DLC metadata stay in CSV files.

```python
from load_arena import LoadArenaProject

project = LoadArenaProject.from_yaml("demo/project/project.yaml")
statistics = project.run_statistics()
uls = project.run_uls()
fls = project.run_fls()
```

Run the portable example with `uv run python demo/project/run_project.py`.
Its PLFs, occurrences, reference count, and Wöhler exponents are illustrative,
not a validated engineering campaign.

- YAML paths are relative to the YAML directory. CSV `Folder` values are relative
  to `data.results_path`; absolute folders remain supported. `Case_folder` stays
  metadata, and `Timeseries` accepts supported filenames or extensionless prefixes.
- Loading validates enabled CSVs and the availability of simulation files and
  companions, without reading time-series samples or creating outputs.
- Analyses default to disabled when omitted. Calling a disabled analysis raises
  `ProjectConfigError`. Each method runs independently and rereads its case CSV.
- Statistics recursively processes HAWC2 `.int`, `.res`, and `.sel` results;
  `.dat` is a companion, and HDF5 and other software are unsupported in this API.
- FLS processes **every numeric channel, including time and non-load signals**,
  for every `wohler_exponents` value. There is no channel-selection configuration.
  `n_ref` is shared; `method` is `windap` (default) or `astm`.
- `Occurrences` means repetitions of the complete recorded simulation. For each
  channel and exponent `m`, campaign DEL is
  `(sum(Occurrences * case_DEL**m))**(1/m)`, using the same `n_ref` for all cases.
  No duration, probability, or lifetime normalization is inferred.
- `FLSResult.per_case` and `.campaign` identify both `channel` and
  `wohler_exponent`. The result also retains `n_ref` and `method`.
- Methods return results and write CSVs in `statistics/`, `uls/`, and `fls/`
  below `output.directory`. Repeated runs replace known CSV outputs and retain
  unrelated files. Output failures raise errors; multi-file writes are not atomic.

Existing family averaging formulas are unchanged. For aggregated family values,
ULS source attribution selects the closest contributing case. Existing reader
channel names and numerical behavior remain authoritative.

## Development

Load Arena is an ongoing personal engineering software project.

I use it both to develop reusable wind turbine load-analysis tools and to improve software-development practices around scientific Python, including:

- modular package structure
- Git-based development
- automated testing with pytest
- CI with GitHub Actions
- dependency management with `uv`
- feature specifications and design notes
- structured scientific data with Xarray and Scipp

The project is under active development and additional post-processing, visualization and data-pipeline features are planned.


## Note:
The code is not done, and it's under development. 


## License

MIT License
