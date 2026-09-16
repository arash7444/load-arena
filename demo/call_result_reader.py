"""Demonstrate portable HAWC2 reading and dataset conversion workflows."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from rich.console import Console

from load_arena.data_reader import (
    read_hawc2_flex,
    to_scipp_dataset,
    to_xarray_dataset,
)


console = Console(markup=False)


def main() -> None:
    """Read a checked-in HAWC2 result and show supported data containers.

    Parameters
    ----------
    None
        The example uses a portable fixture relative to this script.

    Returns
    -------
    None
        Representative Pandas, Xarray, and Scipp information is printed.

    Examples
    --------
    Run the focused reader demo from the repository root:

    >>> # uv run python demo/call_result_reader.py
    """
    source = (
        Path(__file__).parents[1]
        / "tests"
        / "h2_res"
        / "int_res"
        / "dlc13"
        / "dlc13_wsp04_wdir000_s023004"
    )
    dataframe = read_hawc2_flex(source)
    xarray_dataset = to_xarray_dataset(dataframe)
    with redirect_stdout(StringIO()):
        scipp_dataset = to_scipp_dataset(dataframe)

    console.print(f"Source: {source.name}")
    console.print("Pandas sample:")
    console.print(dataframe.head())
    console.print("Xarray dimensions:", dict(xarray_dataset.sizes))
    console.print("Xarray variables:", list(xarray_dataset.data_vars)[:5])
    console.print("Scipp dimensions:", dict(scipp_dataset.sizes))
    console.print("Scipp variables:", list(scipp_dataset.keys())[:5])


if __name__ == "__main__":
    main()
