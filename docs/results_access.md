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

## ULS: global extremes and family results

`uls.ULS` is a one-row global table. `uls.Family_ULS` contains one row per family.
Both contain value/source pairs for `max`, `min`, and `AbsMax`.

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
