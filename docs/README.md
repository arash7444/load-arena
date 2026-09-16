# Load Arena documentation

Use this page to find the current user guides and the historical design records
that explain how Load Arena behaves.

## User guides

- [Project configuration and workflows](project_configuration.md) describes the
  YAML project file, path handling, channel selection, analysis execution, and
  output behavior.
- [Accessing statistics, ULS, and FLS results](results_access.md) documents the
  returned Python objects, plotting helpers, provenance, rainflow results, and
  CSV outputs.
- [Dependency audit](dependency_audit.md) records why each installed dependency
  belongs to the runtime, development, or optional dependency set.

## Design and feature records

- [Tool design](tool_design.md)
- [Project configuration Python API](features/projectConfig_PythonAPI.md)
- [PLF-based ULS calculation](features/plf_uls_calculation_plan.md)
- [Family statistics Family column](features/family_stats_family_column_plan.md)
- [Rainflow, DEL, reader, and input API repairs](bugfix/rainflow_del_reader_input_api_repairs_plan.md)
- [ULS duplicate-channel repair](bugfix/uls_duplicate_channel_names_plan.md)

Files below `features/` and `bugfix/` are implementation records. Use the user
guides above for the current supported workflow.
