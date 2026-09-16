# Obsolete demos

These scripts are retained as historical examples. They use older procedural
APIs, assumptions, or local paths and are not part of the supported release
workflow.

Use these maintained examples instead:

- `demo/project/demo_load_arena.py` for the comprehensive project workflow.
- `demo/call_result_reader.py` for HAWC2 reading and Pandas/Xarray/Scipp
  conversion.

The archived scripts may require adaptation before they can run against the
current package. Their optional seaborn dependency can be installed with
`uv sync --locked --extra demo`.
