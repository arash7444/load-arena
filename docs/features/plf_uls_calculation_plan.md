# PLF-Based ULS Calculation

## Calculation

`calc_uls(family_stats, all_stats)` calculates three independent results per
channel from `family_stats.min_plf` and `family_stats.max_plf`:

- Min: smallest family minimum globally; each family's minimum locally.
- Max: largest family maximum globally; each family's maximum locally.
- AbsMax: whichever Min or Max has the largest magnitude, retaining its sign.

Equal absolute magnitudes prefer Max. Equal values on the same side retain the
first family in input order.

Family aggregation uses the configured method. `mean` averages all samples;
`max` selects the smallest minimum and largest maximum; `mean_half` averages the
smallest half of minima and largest half of maxima. The half size remains
`floor(n / 2)`. These minimum-side corrections apply to raw and PLF family tables.

## Python interface

`ULSStats.ULS` remains a one-row DataFrame without `Family`.
`ULSStats.Family_ULS` remains a DataFrame with a leading `Family` column and one
row per family. Both contain these six columns per channel, in this order:

```python
uls_stats.ULS["max_Load"]
uls_stats.ULS["max_Load_filename"]
uls_stats.ULS["min_Load"]
uls_stats.ULS["min_Load_filename"]
uls_stats.ULS["AbsMax_Load"]
uls_stats.ULS["AbsMax_Load_filename"]
```

Replace `Load` with the actual channel name. These fields replace the former
`Load` / `Load_filename` pair. Duplicate channel names retain the existing
`__2`, `__3`, etc. normalization without modifying input DataFrames.

## Filename attribution

`FamilyAvg.provenance` records one row per family, statistic, PLF mode, and
channel. It retains full member paths as tuples, the files that contributed to
the calculation, the averaging method, and member count. `mean` records all
members as contributors. `mean_half` records the selected half. `max` records
all exact ties and sets `source_file` only when one simulation uniquely governs.

Each ULS Min and Max uses the provenance for its own source side. Aggregate and
tied results use `None` in `*_filename`; no closest simulation is substituted.
AbsMax copies its selected side's exact source, if any. `ULSStats.global_provenance`
records the governing family, side, method, members, contributors, and exact
source. These provenance tables remain in memory and do not alter CSV schemas.

## CSV exports

`LoadArenaProject.run_uls()` writes `uls/global.csv`, with one row per channel:

`ChannelName_ULS | Min_Ultimate_incl_psf | Min_fileName | Max_Ultimate_incl_psf | Max_fileName | AbsMax_Ultimate_incl_psf | AbsMax_fileName`

It also writes `uls/<channel>.csv`, one ranking table per channel:

`Max value | Max Family | Max filename | Min Value | Min Family | Min filename | AbsMax value | AbsMax Family | AbsMax filename`

The three groups rank independently: Max descending, Min ascending, and AbsMax
by magnitude descending with its sign retained. Groups on the same row can
refer to different families. Equal ranks preserve family order.

Invalid Windows filename characters become `_`; trailing dots/spaces are
removed and reserved device names are prefixed with `_`. Case-insensitive name
collisions receive `__2`, `__3`, etc. The names `global` and `family` are reserved.
For example, `WSPgl._[m/s]` exports as `WSPgl._[m_s].csv`.

The combined `family.csv` is no longer written. Existing output files are not
automatically deleted, so an old `family.csv` or obsolete channel CSV can remain
in a previously used output directory.

## Verification

Regression tests cover separate signed extrema and exact source filenames,
PLF-only selection, tied and aggregated provenance, duplicate channels, corrected
family minimum aggregation, the three-family averaging chain, exact export headers,
independent ranking order, and safe filenames. Existing project and family tests
remain applicable.
