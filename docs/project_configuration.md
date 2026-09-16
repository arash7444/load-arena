# Project configuration and workflows

A `LoadArenaProject` represents one simulation campaign. Its YAML file selects
the simulation source, enabled analyses, case tables, channels, and output
directory while CSV files retain per-case metadata.

## Minimal configuration

```yaml
project:
  name: Example HAWC2 Campaign

data:
  software: HAWC2
  results_path: ../../tests/h2_res/int_res

analysis:
  statistics:
    enabled: true
  uls:
    enabled: true
    cases: input/ULS_input_file.csv
    channels: ["WSPgl._[m/s]", "Aerot._[kW]"]
  fls:
    enabled: true
    cases: input/FLS_input_file.csv
    channels: all
    wohler_exponents: [4, 10]
    n_ref: 10000000
    method: windap

output:
  directory: results
```

Load and run each enabled analysis explicitly:

```python
from load_arena import LoadArenaProject

project = LoadArenaProject.from_yaml("demo/project/project.yaml")
statistics = project.run_statistics()
uls = project.run_uls()
fls = project.run_fls()
```

The methods are independent and reread their case CSV when called. Calling a
disabled analysis raises `ProjectConfigError`.

## Paths and input validation

- Relative YAML paths are resolved from the YAML file's directory.
- A case CSV `Folder` is relative to `data.results_path`; absolute folders are
  also accepted.
- `Case_folder` remains metadata. `Timeseries` accepts supported filenames or
  extensionless prefixes.
- Project loading validates enabled case tables, referenced simulations, and
  required companion files. It does not read time-series samples or create an
  output directory.
- Statistics recursively discovers HAWC2 `.int`, `.res`, and `.sel` results.
  A `.dat` file is treated as a companion to `.sel`.

## Channel selection

ULS and FLS accept one of three channel forms:

- An inline list of exact reader column names.
- A CSV path whose `Channel` column contains the selections.
- `all`, which selects every reader channel, including time.

Selections are normalized to unique, nonblank names while preserving their
order. Names must match every referenced simulation exactly, including units and
duplicate-name suffixes. Missing channels identify the failing simulation.

## ULS and family statistics

ULS case rows provide `Family`, `PLF`, and `Averaging_method`. Supported family
methods are `mean`, `max`, and `mean_half`. The latter averages the upper half
for non-minimum statistics and the lower half for minima, using
`floor(member_count / 2)` contributors.

ULS results already include the configured load factors. Exact governing source
paths are recorded only when one simulation uniquely supplies a value;
aggregates and tied extrema use `None` rather than an invented source. See the
[result access guide](results_access.md) and
[ULS schema record](features/plf_uls_calculation_plan.md) for table details.

## FLS, occurrences, and DELs

FLS applies every configured Wöhler exponent to each selected channel. The
method is `windap` by default or `astm`; `n_ref` is shared across the campaign.

`Occurrences` is the number of repetitions of a complete recorded simulation.
For exponent `m`, campaign DEL is calculated as:

```text
(sum(Occurrences * case_DEL**m))**(1/m)
```

No duration, probability, or lifetime normalization is inferred. Per-case
`duration_s` spans the first and last finite, strictly increasing timestamp and
is used as the reference count for the corresponding 1 Hz DEL.

Rainflow counting runs once for each case and channel. The retained cycles are
reused for all configured exponents and later visualization; they are not
exported to CSV.

## Outputs

Configured runs write beneath `output.directory`:

- `statistics/`: mean, standard deviation, minimum, and maximum tables.
- `uls/`: the global table and one family ranking per selected channel.
- `fls/`: the campaign table and one per-case table per selected channel.

Known CSV outputs are replaced on repeated runs while unrelated files remain.
Multi-file writes are not atomic. Output filename sanitization and returned
object schemas are documented in the [result access guide](results_access.md).
