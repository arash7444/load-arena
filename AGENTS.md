# Repository conventions

## Visualization and exploration conventions

- In Plotly user-facing labels and hover text, display only the filename basename using `Path(filename).name`, never the full folder or path.

  Example: `dlc12_seed03.int`, not `D:\project\results\DLC12\dlc12_seed03.int`.

- Keep the original full path unchanged in result and plot metadata for traceability and future interactions, such as opening the corresponding simulation time series.
- Only shorten the displayed text; never modify the stored path.
- Apply these rules consistently to all result exploration features.

## Documentation conventions

- Every function and method, including private helpers, must have a PEP257-style docstring.
- Each docstring must summarize the callable’s purpose and include:
  - Parameters
  - Returns
  - Examples
- Review `docs/results_access.md` for every code change.
- Update `docs/results_access.md` whenever a change affects public APIs, behavior,
  arguments, outputs, or user workflows.
- For internal-only changes, still review the usage guide but leave it unchanged when
  no user-facing guidance is affected.
