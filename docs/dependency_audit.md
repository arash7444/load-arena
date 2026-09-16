# Dependency audit

This audit covers imports in `src/`, tests, demos, and documentation. Runtime
dependencies are required by installed package modules or current public
exports; optional and development dependencies are excluded from a default
installation.

| Dependency | Classification | Repository evidence |
|---|---|---|
| NumPy | Required runtime | Readers, rainflow, DEL, FLS, and utilities use arrays and numerical operations. |
| pandas | Required runtime | Readers, project configuration, statistics, ULS, FLS, and result models use DataFrames. |
| Plotly | Required runtime | Public statistics, family, combined-series, fatigue, and DEL plotting APIs import Plotly. |
| Matplotlib | Required runtime | Installed fatigue and wind-distribution utility modules import Matplotlib. |
| Rich | Required runtime | Installed statistics, family, fatigue, and visualization modules use Rich output. |
| SciPy | Required runtime | Family averaging imports `scipy.spatial.cKDTree`. |
| Numba | Required runtime | Rainflow, peak/trough, and pair/range algorithms use `njit`. |
| Xarray | Required runtime | `load_arena.data_reader` publicly exports `to_xarray_dataset`. |
| Scipp | Required runtime | `load_arena.data_reader` publicly exports `to_scipp_dataset`, which is also tested. |
| Pydantic | Required runtime | Project YAML models and validation use Pydantic. |
| PyYAML | Required runtime | Project configuration loading uses safe YAML parsing. |
| google-genai | Optional/experimental | Only experimental AI tool-calling scripts import it; install with the `ai` extra. |
| pytest | Development/test | The repository test suite uses pytest; package runtime does not. |
| seaborn | Demo dependency | Archived demos import it; install with the optional `demo` extra. |
| OpenPyXL | Unused, removed | No repository code reads or writes Excel workbooks. |

The dependency declarations and `uv.lock` are the authoritative installation
inputs. Re-run this audit when public converter exports or experimental tooling
move into or out of the installed package.
