# PLF-Based ULS Calculation Plan

## Summary

Add a new Ultimate Load / ULS calculation feature outside `FamilyAvg.py`.
`FamilyAvg` should remain unchanged: no ULS fields, no ULS logic, and no changes to the existing `FamilyAvg` dataclass.

ULS values must be calculated from PLF-adjusted family stats: `family_stats.min_plf` and `family_stats.max_plf`.

## Key Changes

- Create a new process module, for example `src/load_arena/process/uls.py`.
- Add a new dataclass, for example `ULSStats`, with:
  - `ULS: pd.DataFrame`: one global row containing the signed absolute-extreme value per channel.
  - `Family_ULS: pd.DataFrame`: one row per family containing the signed absolute-extreme value per channel.
- Add a new function, for example `calc_uls(family_stats: FamilyAvg, all_stats: All_stats) -> ULSStats`.
- Use `family_stats.min_plf` and `family_stats.max_plf` only.
- For each numeric channel, compare `abs(min_plf)` and `abs(max_plf)`.
  - Keep the original signed value with the larger absolute magnitude.
  - If magnitudes are equal, choose the max value.
- `Family_ULS` will preserve the leading `Family` column.
- Global `ULS` will not include `Family`, because it summarizes across all families.
- Add full PEP257 docstrings to every new Python function, including purpose, parameters, returns, and example.

## Filename Provenance

- Add companion filename columns in both outputs.
- For a channel named `Load`, include:
  - `Load`: the ULS numeric value.
  - `Load_filename`: the original source timeseries filename responsible for that ULS value.
- For `Family_ULS`, each family row will identify the original source timeseries that produced the selected PLF min/max for each channel.
- For global `ULS`, each channel filename will come from the family-level row that produced the global extreme.
- Because current `family_stats.min_plf` and `family_stats.max_plf` are family-aggregated rows, exact per-channel source filename provenance cannot always be derived from `family_stats` alone.
- `calc_uls` should therefore accept `all_stats` in addition to `family_stats` so it can map each selected extreme back to the original simulation.

## Public Interface

Export the new dataclass and function from `load_arena.process.__init__`:

- `ULSStats`
- `calc_uls`

Example usage:

```python
family_stats = calc_family_avg(all_stats_hawc2, df_input)
uls_stats = calc_uls(family_stats, all_stats_hawc2)

ULS = uls_stats.ULS
Family_ULS = uls_stats.Family_ULS
```

## Tests

Add focused tests for `calc_uls`:

- Chooses signed minimum when `abs(min_plf) > abs(max_plf)`.
- Chooses signed maximum when `abs(max_plf) >= abs(min_plf)`.
- Produces one global `ULS` row with no `Family` column.
- Produces `Family_ULS` with one row per family and a leading `Family` column.
- Adds `<channel>_filename` companion columns with the selected source timeseries.
- Verifies filename selection separately for min-driven and max-driven ULS values.
- Uses PLF stats only, verified with values where raw stats would produce a different answer.
- Run existing family average tests to confirm no regression.

## Assumptions

- Exact per-channel filename provenance is required, not just the list of files in a family.
- `calc_uls` may accept `all_stats` in addition to `family_stats` to trace ULS values back to original simulations.
- Raw non-PLF ULS tables are out of scope for this version.
