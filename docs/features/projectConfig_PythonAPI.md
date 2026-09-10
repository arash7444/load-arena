# Load Arena project configuration and Python API

## Summary

Introduce a small project layer that validates YAML, resolves paths, and orchestrates existing analysis functions. Keep case definitions in CSV files and engineering calculations in `process`.

Use the requested `project` subpackage. Keep project-level FLS parameters in the main YAML, with multiple shared Wöhler exponents and no channel-selection field. FLS processes **all numeric reader channels, including time**, for every configured exponent.

The inspected baseline was **41 passing tests**. No implementation changes have been made.

## Configuration and public API

Create:

- `src/load_arena/project/config.py`: Pydantic models, YAML loading, and configuration/path validation.
- `src/load_arena/project/project.py`: `LoadArenaProject` and private orchestration/output helpers.
- `src/load_arena/process/fls.py`: campaign FLS processing and `FLSResult`.

Export `LoadArenaProject` through `load_arena.project` and the package root.

Use Pydantic, already a dependency, for nested validation and field-specific errors. Add PyYAML for safe parsing and update the lockfile. Keep reader-level `LoadArenaConfig` unchanged.

| Model | Fields |
|---|---|
| `ProjectConfig` | Root containing `project`, `data`, `analysis`, `output` |
| `ProjectInfo` | Nonblank `name` |
| `DataConfig` | `software`, `results_path` |
| `AnalysisConfig` | `statistics`, `uls`, `fls` |
| `StatisticsConfig` | `enabled` |
| `ULSConfig` | `enabled`, `cases` |
| `FLSConfig` | `enabled`, `cases`, `wohler_exponents`, `n_ref`, `method` |
| `OutputConfig` | `directory` |

Public methods:

- `LoadArenaProject.from_yaml(path) -> LoadArenaProject`
- `run_statistics() -> All_stats`
- `run_uls() -> ULSStats`
- `run_fls() -> FLSResult`

Expose validated configuration as `project.config` and retain the absolute source YAML path. Runs operate independently, without prerequisite ordering, persistent caching, or a primary `run()` method.

Validation:

- Reject malformed YAML, duplicate keys, nonmapping roots, unknown fields, and invalid types. Require actual booleans for `enabled`.
- Require project identity, data location/software, and output directory. Omitted analyses default to disabled.
- Support `HAWC2` only in v1.
- Enabled ULS requires its CSV. Enabled FLS requires its CSV, a nonempty list of positive finite `wohler_exponents`, and positive finite `n_ref`.
- Support `windap` and `astm`; default to `windap` with existing discretization defaults.
- Calling a disabled analysis raises a clear error before computation or output.
- Use `ProjectConfigError(ValueError)` for configuration failures, preserving underlying exceptions and identifying the relevant field, file, or CSV row.

## Paths, workflows, and supporting changes

**Loading and paths**

- Resolve relative YAML paths against the YAML file’s parent directory.
- Resolve relative CSV `Folder` values against `data.results_path`; preserve absolute folders. Join `Timeseries` using `pathlib`. Keep `Case_folder` as metadata.
- Preserve reader-compatible filenames and extensionless prefixes.
- During `from_yaml()`, check the results directory, read and validate enabled case CSVs, and check availability of their referenced simulation files and required companions.
- Do not load time-series data or create output directories during `from_yaml()`.
- Each run rereads its case CSV and rechecks required inputs before processing.
- Validate supplied fields structurally for disabled analyses without requiring their files to exist.

**Statistics**

- Recursively enumerate `.int`, `.res`, and `.sel` files under `results_path`, using existing `find_files` functionality and deterministic sorting.
- Treat `.dat` as a companion to `.sel`; exclude unsupported HDF5.
- Pass the file list to `concatenate_stats`, reusing `ReadHawc2`, `toDataFrame`, and `calc_stats`.
- Return `All_stats` unchanged. Fail clearly when no supported files are found.
- Enumerate result files without inferring DLC definitions.

**ULS**

Reuse this pipeline:

1. `read_uls_input_file()`.
2. Normalize case paths and perform input preflight.
3. `concatenate_stats()`.
4. `calc_family_avg()`.
5. `calc_uls()`.

Return `ULSStats` unchanged. ULS computes its required statistics even when standalone statistics is disabled.

**FLS**

- Read cases with `read_fls_input_file()`.
- Implement campaign processing in `process/fls.py`, reusing `ReadHawc2`/`toDataFrame` and `calc_del`.
- Process every numeric reader channel, including time, for each configured Wöhler exponent. Do not infer load-channel categories.
- Use the shared `n_ref` and configured rainflow method for all channel/exponent combinations.
- Interpret finite nonnegative `Occurrences` as repetitions of the complete recorded simulation.
- For each channel and exponent `m`, calculate per-case DELs and aggregate:

  `campaign_DEL = (sum(Occurrences × case_DEL**m))**(1/m)`

- Keep channel/exponent combinations separate throughout calculation and aggregation.
- Do not add probability generation, lifetime inference, duration normalization, or transient trimming.
- Define `FLSResult` with `per_case` and `campaign` DataFrames. Per-case rows identify case row, resolved filename, channel, Wöhler exponent, occurrences, and DEL. Campaign rows identify channel, Wöhler exponent, and DEL. Retain reference count and method as result metadata.
- Preserve existing zero-cycle and invalid-signal behavior. Do not copy the flawed demo aggregation.

**Outputs**

Return structured results and write CSVs after successful calculation:

- `statistics/`: mean, standard deviation, minimum, and maximum tables with filename identity.
- `uls/`: global and family ULS tables with source filename columns.
- `fls/`: per-case and campaign DEL tables identifying both channel and Wöhler exponent, with reference count and method.

Create directories lazily. Repeat runs replace only known output files and preserve unrelated files. Propagate write failures clearly; transactional multi-file export remains outside v1.

**Limited supporting fixes**

- Replace statistics CSV path string concatenation with `pathlib` joins.
- Use explicit ULS validation in statistics/family averaging.
- Check empty case tables, required row values, positive finite PLFs, and valid family averaging methods. Reject single-case `mean_max` groups because their current calculation selects zero rows.
- Preserve engineering formulas, existing return types, and legacy entry points.
- Correct CI’s missing `requirements.txt` installation/cache reference to use `pyproject.toml`; include dependency-file changes in CI triggers.
- Give every new or modified Python function a PEP257 docstring containing purpose, Parameters, Returns, and Examples.

## Tests and existing risks

Add tests covering:

- YAML structure, duplicate/unknown keys, booleans, software, enabled requirements, invalid exponent lists, and invalid reference counts.
- Relative/absolute paths, missing separators, extensionless cases, and execution from another working directory.
- CSV and simulation availability checks during `from_yaml()`, without time-series reads or output creation.
- Disabled-method errors.
- Statistics discovery, deterministic ordering, empty directories, and missing companions.
- Project ULS parity with the existing direct pipeline, including PLFs, family grouping, and filename attribution.
- FLS across multiple cases, numeric channels, and exponents; inclusion of time; exclusion of nonnumeric columns; unequal/zero occurrences; both counting methods; known weighted results; and invalid signals.
- FLS result/export identity by both channel and exponent.
- Return types, CSV contents, repeat-run replacement, unrelated-file preservation, and output failures.
- The complete regression suite and Python 3.10 CI.

Retain these documented limitations:

- Campaign FLS aggregation is new orchestration around tested primitives; the demo is not a numerical reference.
- Family averaging formulas remain unchanged. ULS attribution uses the closest contributing case for aggregated family values.
- Existing CSV fixtures contain machine-specific paths; new tests/examples use portable paths.
- Existing readers and aggregation determine channel compatibility and numerical behavior. Broader cleanup remains outside scope.

## Minimal example project

Add `demo/project/` with YAML, portable ULS/FLS CSVs, and a noninteractive Python example referencing checked-in HAWC2 fixtures.

```yaml
project:
  name: Example HAWC2 Campaign

data:
  software: HAWC2
  results_path: ../../tests/h2_res/dlc13

analysis:
  statistics:
    enabled: true
  uls:
    enabled: true
    cases: input/ULS_cases.csv
  fls:
    enabled: true
    cases: input/FLS_cases.csv
    wohler_exponents: [4, 6, 8, 10, 12]
    n_ref: 10000000
    method: windap

output:
  directory: results
```

Use `Folder` values of `.` in example CSV rows, existing case names, and explicitly illustrative engineering values.

The example locates YAML relative to its own script, calls all three methods explicitly, and shows returned results and CSV locations. Document path rules, enabled flags, occurrence semantics, all-numeric-channel processing, multiple exponents, and output replacement.

No GUI, CLI, LLM integration, automatic DLC discovery, reporting system, additional fatigue products, or unrelated refactoring is included.
