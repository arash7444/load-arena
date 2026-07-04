# ULS Duplicate Channel Names Bugfix Plan

## Summary

Fix the ULS bug caused by duplicate channel names in pandas DataFrames.
When duplicate column labels exist, expressions such as `min_row[channel]` can return a Series instead of a scalar, causing this error:

```text
ValueError: The truth value of a Series is ambiguous.
```

The preferred fix is to make channel names unique when data is first converted to a DataFrame.

## Key Changes

- Update `toDataFrame(...)` in `src/load_arena/data_reader/Hawc2io.py` so generated column names are unique before creating the pandas DataFrame.
- Add a helper function, for example `_make_unique_columns(columns: list[str]) -> list[str]`, with a full PEP257 docstring.
- Apply the helper after names and units are combined, so duplicates are detected on the final displayed channel name.
- Keep the first occurrence unchanged and suffix later duplicates:
  - `Aerot._[kW]`
  - `Aerot._[kW]__2`
  - `Aerot._[kW]__3`
- Update `uls.py` defensively so it no longer relies on ambiguous duplicate labels if a user passes manually built duplicate-column DataFrames.

## ULS Behavior

- `_choose_extreme(...)` should continue to receive scalar values only.
- `Family_ULS` should include each unique channel column and its filename companion:
  - `Load`
  - `Load_filename`
  - `Load__2`
  - `Load__2_filename`
- Global `ULS` should use the same unique channel names and companion filename columns.
- Existing ULS logic remains unchanged:
  - use PLF stats
  - compare absolute min and max
  - preserve the signed extreme value
  - choose max when absolute values are tied

## Tests

- Add a test for `toDataFrame(...)` where two channels would produce the same final name and confirm suffixes are applied.
- Add a ULS regression test using duplicate original channel names, verifying:
  - no ambiguous Series truth-value error is raised
  - both duplicate channels are present as separate ULS columns
  - each duplicate channel has the correct ULS value and filename column
- Run the full test suite to confirm existing stats and family average behavior still works.

## Assumptions

- It is acceptable that all downstream outputs now see unique suffixed channel names instead of duplicate pandas columns.
- Suffixing starts at `__2`; the first channel keeps its original name.
- Wide DataFrame output remains preferred over MultiIndex or long-format ULS output because it keeps plotting and demo usage simple.
