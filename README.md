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

# Inspect or plot the original family-average result used by ULS.
family_stats = uls.family_stats
figure = family_stats.explore(
    channel="WSPgl._[m/s]", statistic="max", show=False,
)
```

For examples of selecting channels, files, families, DELs, and stored rainflow
cycles, see the [result access guide](docs/results_access.md).

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
- Enabled ULS and FLS sections require `channels`: an inline list such as
  `channels: ["WSPgl._[m/s]"]`, a CSV path such as `channels: input/channels.csv`,
  or `channels: all` to include every channel in each simulation (including time).
  The CSV must contain a `Channel` column. Paths are relative to the YAML file;
  both forms normalize to a nonempty list of unique, nonblank names. Names match
  reader columns exactly, including units and duplicate-name suffixes. Each run
  checks the selection in every referenced simulation and processes only those
  channels, in selection order. Missing channels raise an error identifying the file.
- FLS applies every `wohler_exponents` value to the selected channels. Time and
  other numeric columns are included when explicitly selected or with `channels: all`. `n_ref` is
  shared; `method` is `windap` (default) or `astm`. Direct `calc_fls()` calls also
  require the `channels` keyword argument.
- `Occurrences` means repetitions of the complete recorded simulation. For each
  channel and exponent `m`, campaign DEL is
  `(sum(Occurrences * case_DEL**m))**(1/m)`, using the same `n_ref` for all cases.
  No duration, probability, or lifetime normalization is inferred.
- FLS results are organized by channel:
  `channel = result.channels["TowerMy_[kNm]"]`. Each channel contains:
  `channel.files` (one row per input case), `channel.rainflow_results[case_row]`
  (complete unbinned cycles), and `channel.campaign` (Wöhler exponent and DEL).
  Shared parameters remain `result.n_ref` and `result.method`. The old flat
  `per_case`, `campaign`, and `rainflow_results` fields have been removed.
- Each channel's file table contains `case_row`, `filename`, `occurrences`, and
  `duration_s`, then pairs such as `DEL_m4`, `DEL_1Hz_m4`, `DEL_m10`, `DEL_1Hz_m10`
  in configured exponent order. Fractional exponents retain their shortest
  round-trip float spelling. CSV row numbers distinguish repeated filenames.
- `duration_s` spans the first and last reader timestamps and supplies the
  reference count for 1 Hz DEL. Timestamps must be finite, strictly increasing,
  and contain at least two values; time need not be a selected channel.
- FLS writes one safely named channel CSV with the file table plus `n_ref` and
  `method`. Combined `campaign.csv` retains its existing summary schema. Channel
  filenames follow ULS sanitization and collision rules, reserving `campaign`
  and `per_case`. Existing output files are retained: an old `per_case.csv` is
  obsolete and is no longer updated.
- Rainflow counting runs once per case/channel; full ranges, means, counts, and
  counting parameters stay in memory and are reused for all exponents and both
  DEL references. These results support later spectra, damage contribution
  plots, and Markov matrices; rainflow data is not exported to CSV.
- `calc_del_from_rainflow(result, wohler_exponent, n_ref)` calculates DEL from a
  retained rainflow result without recounting cycles. Existing `calc_del()` calls
  and campaign occurrence weighting remain unchanged.
- ULS exports `uls/global.csv` with one row per channel and a separate CSV per
  channel with independent Max, Min, and signed AbsMax family rankings. See
  [ULS calculation and output schemas](docs/features/plf_uls_calculation_plan.md).
- Methods return results and write CSVs in `statistics/`, `uls/`, and `fls/`
  below `output.directory`. Repeated runs replace known CSV outputs and retain
  unrelated files. Output failures raise errors; multi-file writes are not atomic.

Family averaging supports `mean`, `max`, and `mean_half`; `mean_half` averages
the upper half for non-minimum statistics and the lower half for minima, using
`floor(n / 2)` members. `FamilyAvg.provenance` retains full member and contributor
paths. ULS filename fields contain a path only when one exact simulation uniquely
governs the family value; aggregated and tied values use `None` instead of an
invented representative filename. Existing reader channel names remain authoritative.

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
