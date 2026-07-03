# Add Family Columns To Family Statistics

## Summary

Add the family identifier directly into every `FamilyAvg` statistics dataframe so users can filter, group, plot, and modify `family_stats.mean`, `family_stats.std`, `family_stats.max`, `family_stats.min`, and the PLF variants by family. Keep `family_stats.family_name` available as a backward-compatible alias/list.

## Key Changes

- In `calc_family_avg`, after computing each per-family dataframe row, add a normal `Family` column before concatenating into `mean`, `std`, `min`, `max`, `mean_plf`, `std_plf`, `min_plf`, and `max_plf`.
- Put `Family` as the first column in each output dataframe for easy scanning and `groupby("Family")` usage.
- Continue appending to `family_stats.family_name`, `family_stats.filename`, and `family_stats.case_folder` so existing user code and tests still work.
- Update the demo output to show dataframe-based family usage, while optionally leaving the old `family_stats.family_name` print as compatibility evidence.
- Do not add new Python functions unless needed. If one is introduced during implementation, it must include a PEP257 docstring with purpose, Parameters, Returns, and an example.

## Tests

- Update `test_calc_family_avg_mean_collects_family_metadata` to assert that `family_stats.mean["Family"].iloc[0] == 1`.
- Assert that `family_stats.std`, `family_stats.min`, `family_stats.max`, and all PLF dataframes also contain `Family`.
- Keep the existing backward compatibility assertion that `family_stats.family_name == [1]`.
- Add or extend a multiple-family test to verify one output row per family, `family_stats.mean.groupby("Family")` works as expected, and numeric statistic columns remain unchanged after adding the metadata column.
- Run the focused test file, then the full test suite if feasible.

## Assumptions

- The canonical dataframe column name should be `Family`, matching the input file column.
- `Family` should be a normal column, not an index.
- Backward compatibility is desired, so `family_stats.family_name` remains available for now.
