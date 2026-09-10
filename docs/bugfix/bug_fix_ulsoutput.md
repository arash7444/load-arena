# Correct ULS calculations and CSV outputs

Implemented. See [current calculation and CSV schemas](../features/plf_uls_calculation_plan.md).
Existing output files are preserved; legacy `family.csv` is no longer written.

## Calculation changes

- Calculate separate signed Min, Max, and AbsMax results for every channel, globally and per family, using PLF-adjusted statistics.
- Global Min selects the smallest family minimum; Global Max selects the largest family maximum. AbsMax selects the largest magnitude and retains its sign.
- Correct family minimum aggregation: `max` selects the smallest minimum; `mean_max` averages the smallest half of minima. Keep `mean` and maximum-side aggregation unchanged.
- Preserve the closest-source filename rule for averaged values. Equal-distance matches retain the first source filename.

## Internal results

Keep `ULSStats.ULS` and `ULSStats.Family_ULS` as DataFrames, with six fields per channel:

- `max_<channel>` and `max_<channel>_filename`
- `min_<channel>` and `min_<channel>_filename`
- `AbsMax_<channel>` and `AbsMax_<channel>_filename`

Global results retain one row; family results retain one row per family with its `Family` identifier. Replace the old single-extreme fields and update existing consumers.

## CSV outputs

**Global:** one row per channel, matching the screenshot’s exact column order:

`ChannelName_ULS | Min_Ultimate_incl_psf | Min_fileName | Max_Ultimate_incl_psf | Max_fileName | AbsMax_Ultimate_incl_psf | AbsMax_fileName`

**Family:** replace the combined family CSV export with one CSV per channel, containing:

`Max value | Max Family | Max filename | Min Value | Min Family | Min filename | AbsMax value | AbsMax Family | AbsMax filename`

Rank the three groups independently: Max descending, Min ascending, and AbsMax by magnitude descending. Different groups may identify different families on the same row.

Sanitize invalid filename characters to `_`, preserving the original channel names in calculation results. Add numeric suffixes for filename collisions.

## Implementation and verification

- Modify existing calculation, aggregation, export, and demo functions; add Python functions only if necessary.
- Update the calculation plan and affected docstrings. Any new function must include purpose, Parameters, Returns, and Examples.
- Extend existing tests to cover independent extrema and filenames, signed AbsMax, corrected minimum aggregation, averaged-value provenance, duplicate channels, CSV headers, independent rankings, and safe filenames.
- Run ULS, family-average, and project-export tests.

Defaults: preserve existing family/source order for equal ranking values; prefer Max when Min and Max have equal absolute magnitude. Keep existing averaging group sizes and PLF application unchanged.

## Verification result

Full test suite: 91 passed. Tests used a workspace temporary directory because
the default Windows pytest temporary directory was inaccessible. No new Python
functions were added.
