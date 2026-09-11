## Visualization / exploration conventions

- In Plotly hover text, show only the file basename, not the full path.
  Example:
  `dlc12_seed03.int`
  not:
  `D:\project\results\DLC12\dlc12_seed03.int`

- Keep the full original path in stored result metadata for traceability.
- Only shorten the displayed hover text.
- Apply this consistently to all result exploration features.

## Visualization metadata:
 User-facing labels and hover text should display only file basenames for readability.
 The full original file path must remain available in the result/plot metadata so future interactions such as clicking a point and opening the corresponding simulation time series can locate the source file.
  
  ## Documentation conventions

- Every function and method, including private helpers, should have a PEP257-style docstring.
- Docstrings should include:
  - purpose
  - Parameters
  - Returns
  - Examples where meaningful