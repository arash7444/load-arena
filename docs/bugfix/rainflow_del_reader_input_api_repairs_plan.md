# Rainflow, DEL, Reader, and Input API Repairs

## Summary

- Do not modify `demo/call_DEL_full.py`.
- Treat a finite constant signal as valid zero-fatigue data: emit `RuntimeWarning`, return zero cycles, and calculate DEL as `0.0`.
- Keep `calc_del` compatible with raw signals and add an explicit Windap/ASTM method argument.

## Implementation Changes

- Make `RainflowResult` a real dataclass instance containing a float-typed `cycles` DataFrame plus `method`, `levels`, and `threshold`. Expose `range`, `mean`, and `count` as read-only properties.
- Make `calculate_rainflow` accept NumPy arrays and pandas Series, return independent results, validate dimensions/types/finite values and Windap parameters, and reject missing values rather than joining signal segments across gaps.
- For a finite signal with no variation, issue `warnings.warn(..., RuntimeWarning, stacklevel=2)` and return an empty DataFrame with `range`, `mean`, and `count` columns. A single finite sample follows the same behavior.
- Keep `calc_del` signal-based: `calc_del(signal, wohler_exponent, n_ref, method="windap", levels=255, threshold=255/50)`. Validate positive finite DEL parameters, call `calculate_rainflow` with the selected method, and return `0.0` when no cycles exist.
- Clean only `src/load_arena/process/calc_del.py`: remove unused Matplotlib, HAWC2, Rich, statistics, pandas, and `signal.signal` imports; remove import-time traceback installation and the embedded `__main__` demonstration; use direct submodule imports to avoid package initialization cycles. This does not delete or alter HAWC2 reader or demo files.
- Fix the HAWC2 reader separately: import `Path` correctly, accept path-like inputs on Python 3.10+, honor the supplied SEL path, and keep fixture-specific azimuth assertions only in tests.
- Add explicit ULS/FLS validation modes, reject ambiguous schemas, and restore `read_input_file` as a deprecated ULS alias. Update callers outside `call_DEL_full.py` to the explicit API.

## Public Interfaces

- `calculate_rainflow(signal, method="windap", levels=255, threshold=255/50) -> RainflowResult`
- `RainflowResult.cycles` always contains float columns `range`, `mean`, and `count`, including when empty.
- `calc_del(signal, wohler_exponent, n_ref, method="windap", levels=255, threshold=255/50) -> float`
- ASTM ignores Windap-only parameters and records `levels=None` and `threshold=None` in its result metadata.
- `validate_input_columns(df, mode: Literal["uls", "fls"] | None = None) -> None`
- `read_input_file` remains temporarily available as a deprecated alias.

## Test Plan

- Add asserted ASTM and Windap reference cases, result-schema checks, and repeat-call isolation tests.
- Verify constant and single-value signals warn, return empty cycles, and produce DEL `0.0`; all-NaN, partly missing, infinite, nonnumeric, and multidimensional inputs remain errors.
- Test DEL for both methods, known manual damage calculations, invalid reference/exponent values, and Windap parameter forwarding.
- Test HAWC2 readers with caller-supplied fixture paths and verify no data-specific assertions remain in library code.
- Test valid, malformed, and ambiguous ULS/FLS inputs and the deprecated compatibility alias.
- Run the complete suite under the existing Python 3.10 CI configuration.

## Assumptions

- NaN means missing or invalid data; it is not used to represent a valid zero-fatigue result.
- The warning is emitted once per constant-signal call and remains filterable through Python's standard warnings system.
- `demo/call_DEL_full.py`, including its current uncommitted work, remains untouched.
- This document records the plan only; none of the planned bug fixes are implemented as part of updating it.
