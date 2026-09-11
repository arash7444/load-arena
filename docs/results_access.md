# Accessing statistics, ULS, and FLS results

A practical reference for the current Python API. Run examples from the repository
root, using a YAML file with the analyses you want enabled. Each `run_*()` call
calculates results and writes its configured CSV outputs; accessing the returned
objects afterwards does not rerun the analysis.

## Run the analyses

```python
import pandas as pd
from load_arena import LoadArenaProject

project = LoadArenaProject.from_yaml("demo/project/project.yaml")
statistics = project.run_statistics()
uls = project.run_uls()
fls = project.run_fls()
```

Each analysis runs independently. ULS and FLS use their own channel selections.
Use the exact channel names returned by the reader, including units and suffixes.
The examples below pick an available channel automatically; replace it with a
specific name from the printed list when needed.

## Statistics: channel values across simulation files

`statistics.mean`, `.std`, `.min`, and `.max` are DataFrames with one row per
simulation and one column per channel. `statistics.filename` is a separate list
in the same row order.

```python
print(statistics.mean.columns.tolist())  # Available channels
print(statistics.filename)               # Simulation paths

name = statistics.mean.columns[0]        # Or an exact name from the list
print(statistics.mean[name])             # This channel's mean for every file
print(statistics.max[name])              # This channel's maximum for every file

# Join filenames and all four statistics for one channel.
channel_stats = pd.DataFrame({
    "filename": statistics.filename,
    "mean": statistics.mean[name],
    "std": statistics.std[name],
    "min": statistics.min[name],
    "max": statistics.max[name],
})
print(channel_stats)

# Access one simulation by its position, or by its exact full filename.
position = 0
print(statistics.filename[position])
print(statistics.mean[name].iloc[position])
filename = statistics.filename[position]
print(channel_stats.loc[channel_stats["filename"] == filename])
```

The object also has `mean_plf`, `std_plf`, `min_plf`, and `max_plf`. Standalone
`run_statistics()` uses a factor of 1, so these equal the corresponding raw tables.
It does not apply the ULS case CSV's PLFs. Its `family` list contains placeholder
values because standalone statistics discovers files rather than loading families.

## Explore statistics interactively

Use the statistics result already calculated by the project:

```python
statistics = project.run_statistics()
print(statistics.mean.columns.tolist())
fig = statistics.explore(channel="Aerot._[kW]", statistic="mean")
# Suppress display when building a figure for later use:
fig = statistics.explore(channel="Aerot._[kW]", statistic="max", show=False)
```

Use exact reader channel names. There is no additional calculation entry point
or second list of simulation files to provide.

`explore()` requires one channel and one of `mean`, `std`, `min`, or `max`.
It returns a Plotly Figure and displays it by default, with hover, zoom, and
legend controls. No channel/statistic dropdowns or application GUI are involved.

By default, the x-axis is the zero-based simulation row in `statistics.filename` order.
To use an existing channel for x, select its statistic independently:

```python
fig = statistics.explore(
    channel="TowerMy_[kNm]",
    statistic="max",
    x_channel="WSPgl._[m/s]",
    x_statistic="mean",
    kind="scatter",
)
```

Both axes use stored statistics paired by simulation row, even if their DataFrame
index labels differ. Here x is the measured mean wind speed, not nominal input
wind speed. `x_statistic` defaults to `"mean"` and accepts the same four statistics
as y; it is unused when `x_channel` is omitted.

`kind` accepts `"scatter"` (default), `"bar"`, or `"line"`. Lines connect points in
ascending x order, retaining input order for equal x values. Scatter and bar retain
simulation order. Equal x values are never aggregated; bars at the same numeric x
can overlap. Filename hover information stays paired with the original simulation.

Hover over a point to inspect its filename and value. Hover text displays only
the filename basename for readability; the original full path remains unchanged
in the result and Plotly metadata. Repeated filenames remain separate points,
and DataFrame index labels do not affect positional alignment. No extra metadata
or simulation inputs are required. `All_stats.explore()` does not parse filenames,
group simulations, or calculate family averages.
Invalid selections, empty results, mismatched filename counts, and nonfinite
selected values raise `ValueError` without silently dropping rows.

Exploration uses stored raw statistics; it neither rereads simulations nor changes
the result tables. Existing `.mean`, `.std`, `.min`, and `.max` access is unchanged.

## Explore family averages interactively

`project.run_uls()` returns one `ULSStats` object and exposes the stored
`FamilyAvg` calculation as `uls.family_stats`. No separate calculation is needed:

```python
uls = project.run_uls()
family_stats = uls.family_stats

print(family_stats.mean.columns.tolist())
print(family_stats.family_name)
```

Explore an exact channel using one of `mean`, `std`, `min`, or `max`. The default
x-axis is the stored `Family` column, with one unconnected marker per family:

```python
fig = family_stats.explore(
    channel="TowerMx_[kNm]",
    statistic="max",
)

# Build and return the same kind of figure without displaying it.
fig = family_stats.explore(
    channel="TowerMx_[kNm]",
    statistic="max",
    show=False,
)
```

Set `plf=True` to select the corresponding stored PLF-adjusted table:

```python
fig = family_stats.explore(
    channel="TowerMx_[kNm]",
    statistic="max",
    plf=True,
)
```

The `x` argument can instead name another exact channel. Both numeric axes use
the same selected statistic and PLF mode and remain aligned by stored family row:

```python
fig = family_stats.explore(
    x="WindSpeed_[m/s]",
    channel="TowerMx_[kNm]",
    statistic="mean",
    plf=False,
)
```

The figure title identifies the statistic and whether the selected data is raw or
PLF-adjusted. Hover text shows the family, value, exact channel, statistic, PLF
status, and the basenames of files belonging to that family. Full file paths remain
available in the stored result and Plotly metadata.

Exploration only visualizes the selected `FamilyAvg` table. It does not call
`calc_family_avg()`, reread simulations, recalculate values, reorder families, or
modify stored data. Invalid statistics, non-Boolean `plf`, missing or duplicate
channels, empty results, inconsistent family metadata, and nonnumeric or nonfinite
selected channel values raise `ValueError`.

Calculated results from `project.run_uls()` and `calc_uls()` always provide
`family_stats`. The field is optional only so legacy code can still construct
`ULSStats(ULS=..., Family_ULS=...)` directly.

## ULS: global extremes and family results

`uls.ULS` is a one-row global table. `uls.Family_ULS` contains one row per family,
and `uls.family_stats` contains the original family-average calculation used to
produce those ULS results. The ULS tables contain value/source pairs for `max`,
`min`, and `AbsMax`.

```python
# Each channel occupies six columns: three values and their source filenames.
uls_names = [column.removeprefix("max_") for column in uls.ULS.columns[::6]]
print(uls_names)
name = uls_names[0]

print(uls.ULS)           # Global results across all selected channels
print(uls.Family_ULS)    # Results for every family

# Global values and their attributed simulation files for one channel.
for side in ("max", "min", "AbsMax"):
    print(side, uls.ULS[f"{side}_{name}"].iloc[0])
    print("Source:", uls.ULS[f"{side}_{name}_filename"].iloc[0])

columns = [
    f"{side}_{name}{suffix}"
    for side in ("max", "min", "AbsMax")
    for suffix in ("", "_filename")
]
family_results = uls.Family_ULS[["Family", *columns]]
print(family_results)

family_id = family_results["Family"].iloc[0]
print(family_results.loc[family_results["Family"] == family_id])

# Rank families by absolute magnitude while preserving signed values.
ranking = family_results.sort_values(
    f"AbsMax_{name}", key=lambda values: values.abs(), ascending=False,
)
print(ranking)
```

`AbsMax` retains the sign of the governing extreme. ULS values already include
the configured load factors and family processing; do not multiply them again.
For averaged family values, source attribution identifies the closest contributing
simulation. The exported global CSV has a different, channel-per-row layout from
`uls.ULS`; see [ULS output schemas](features/plf_uls_calculation_plan.md).

## FLS: select a channel, then access its files and cycles

```python
print(list(fls.channels))
name = next(iter(fls.channels))
# For a specific channel, use its exact name from the list, for example:
# name = "TowerMy_[kNm]"
channel = fls.channels[name]

print(channel.files)       # One row per input simulation case
print(channel.campaign)    # Campaign DEL for each exponent
print(fls.n_ref)           # Configured reference cycle count
print(fls.method)          # "windap" or "astm"
```

### DELs for all files or one case

`channel.files` starts with `case_row`, `filename`, `occurrences`, and `duration_s`.
Each configured exponent adds two columns, such as `DEL_m4` and `DEL_1Hz_m4`.

```python
print(channel.files.columns.tolist())

# Pick an available exponent, preserving its column-label spelling.
m = float(channel.campaign["wohler_exponent"].iloc[0])
label = repr(m).removesuffix(".0")
del_column = f"DEL_m{label}"
del_1hz_column = f"DEL_1Hz_m{label}"

print(channel.files[["filename", "duration_s", del_column, del_1hz_column]])

case_row = int(channel.files["case_row"].iloc[0])
file_result = channel.files.set_index("case_row").loc[case_row]
print(file_result["filename"])
print(file_result[del_column])
print(file_result[del_1hz_column])

# Filename lookup may return multiple cases referencing the same file.
filename = file_result["filename"]
print(channel.files.loc[channel.files["filename"] == filename])

# Campaign DEL uses the configured n_ref and occurrence weighting.
campaign_del = channel.campaign.set_index("wohler_exponent").loc[m, "DEL"]
print(campaign_del)
```

`case_row = 2` identifies the first data row of the FLS input CSV (header is row 1).
It is not the DataFrame's zero-based index. Repeated filenames remain distinct
cases. `duration_s` is the last minus first reader timestamp; `DEL_1Hz_m...` uses
that duration in seconds as its reference cycle count. Campaign DELs are not
1 Hz DELs and are not simple averages of the file DELs.

### Retrieve stored rainflow counting results

```python
rainflow = channel.rainflow_results[case_row]
print(rainflow.cycles)       # DataFrame: range, mean, count
print(rainflow.range)        # Series of cycle ranges
print(rainflow.mean)         # Series of cycle means
print(rainflow.count)        # Series of cycle counts
print(rainflow.method)
print(rainflow.levels)       # Windap setting; None for ASTM
print(rainflow.threshold)    # Windap setting; None for ASTM

# Calculate DEL for another reference count without recounting cycles.
from load_arena.process import calc_del_from_rainflow
recomputed_del = calc_del_from_rainflow(rainflow, wohler_exponent=m, n_ref=fls.n_ref)
print(recomputed_del)

# Iterate over all channels and their file results.
for channel_name, channel_result in fls.channels.items():
    print(channel_name)
    print(channel_result.files)
    print(channel_result.campaign)
```

Rainflow data stays in memory and is shared across exponent calculations for that
case/channel. Constant signals retain an empty cycle table and zero DELs.
There are no top-level `fls.per_case`, `fls.campaign`, or `fls.rainflow_results`
fields; access everything through `fls.channels[name]`.

## Find and read output CSVs

```python
output = project.config.output.directory
print(output)

saved_means = pd.read_csv(output / "statistics" / "mean.csv")
saved_uls_global = pd.read_csv(output / "uls" / "global.csv")
saved_fls_campaign = pd.read_csv(output / "fls" / "campaign.csv")
print(sorted(path.name for path in (output / "fls").glob("*.csv")))
```

| Directory | Files |
|---|---|
| `statistics/` | `mean.csv`, `std.csv`, `min.csv`, `max.csv`, with filenames included |
| `uls/` | `global.csv` and one family-ranking CSV per selected channel |
| `fls/` | `campaign.csv` and one wide file-results CSV per selected channel, with `n_ref` and `method` appended |

Channel filenames are sanitized: for example, `WSPgl._[m/s]` becomes
`WSPgl._[m_s].csv`. Reserved names and collisions can add prefixes or suffixes;
inspect the directory rather than assuming the exact channel name is a filename.
Existing files are preserved. An old `fls/per_case.csv` is obsolete and is no
longer updated. Rainflow cycle tables are not exported to CSV.
