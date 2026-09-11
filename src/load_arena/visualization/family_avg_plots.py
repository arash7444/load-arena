"""Interactive exploration of stored family-average statistics."""

from math import isfinite
from numbers import Real
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go


if TYPE_CHECKING:
    from load_arena.process.family_avg import FamilyAvg


def _selected_table(stats: "FamilyAvg", statistic: str, plf: bool) -> pd.DataFrame:
    """Select and validate one stored family-average table.

    Parameters
    ----------
    stats : FamilyAvg
        Stored family-average result.
    statistic : str
        Requested statistic name.
    plf : bool
        Whether to select the PLF-adjusted variant.

    Returns
    -------
    pandas.DataFrame
        Selected nonempty table without copying or mutation.

    Examples
    --------
    >>> table = _selected_table(family_stats, "max", False)
    """
    if not isinstance(statistic, str) or statistic not in ("mean", "std", "min", "max"):
        raise ValueError("statistic must be one of: mean, std, min, max.")
    if not isinstance(plf, bool):
        raise ValueError("plf must be a bool.")
    table_name = f"{statistic}_plf" if plf else statistic
    table = getattr(stats, table_name)
    if not isinstance(table, pd.DataFrame):
        raise ValueError(f"FamilyAvg.{table_name} must be a pandas DataFrame.")
    if table.empty:
        raise ValueError("FamilyAvg exploration requires at least one family.")
    return table


def _numeric_values(table: pd.DataFrame, channel: str, axis: str) -> list[Real]:
    """Extract one exact channel and require finite numeric values.

    Parameters
    ----------
    table : pandas.DataFrame
        Selected family-average table.
    channel : str
        Exact channel column name.
    axis : str
        Axis label used in validation errors.

    Returns
    -------
    list of numbers.Real
        Values in stored family row order.

    Examples
    --------
    >>> values = _numeric_values(table, "TowerMx_[kNm]", "y")
    """
    if not isinstance(channel, str) or list(table.columns).count(channel) != 1:
        raise ValueError(
            f"{axis}-axis channel must identify exactly one column in the selected "
            f"FamilyAvg table; received {channel!r}. Available columns: {list(table.columns)!r}"
        )
    values = table[channel].tolist()
    for row, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError(
                f"{axis}-axis value for channel {channel!r} at family row {row} "
                "must be a finite numeric value."
            )
    return values


def _family_values(stats: "FamilyAvg", table: pd.DataFrame) -> list:
    """Validate and return authoritative family labels from the selected table.

    Parameters
    ----------
    stats : FamilyAvg
        Stored family-average result containing legacy family metadata.
    table : pandas.DataFrame
        Selected family-average table containing the authoritative Family column.

    Returns
    -------
    list
        Family labels in stored table row order.

    Examples
    --------
    >>> families = _family_values(family_stats, family_stats.mean)
    """
    if list(table.columns).count("Family") != 1:
        raise ValueError(
            "The selected FamilyAvg table must contain exactly one 'Family' column."
        )
    families = table["Family"].tolist()
    if len(stats.family_name) != len(table):
        raise ValueError(
            f"family_name must contain one entry per family ({len(table)} entries)."
        )
    if not pd.Series(families, dtype=object).equals(
        pd.Series(list(stats.family_name), dtype=object)
    ):
        raise ValueError("The Family column must align with family_name in stored row order.")
    return families


def _filename_metadata(stats: "FamilyAvg", count: int) -> tuple[list[str], list[list[str]]]:
    """Prepare basename hover labels while retaining full stored file paths.

    Parameters
    ----------
    stats : FamilyAvg
        Stored result whose filename entry belongs to each family row.
    count : int
        Expected number of family rows.

    Returns
    -------
    tuple of list[str] and list[list[str]]
        Readable basename strings and unchanged full-path strings per family.

    Examples
    --------
    >>> labels, paths = _filename_metadata(family_stats, 2)
    """
    if len(stats.filename) != count:
        raise ValueError(f"filename must contain one entry per family ({count} entries).")
    labels = []
    full_paths = []
    for row, filenames in enumerate(stats.filename):
        if isinstance(filenames, (str, bytes)) or hasattr(filenames, "__fspath__"):
            family_paths = [str(filenames)]
        else:
            try:
                family_paths = [str(filename) for filename in filenames]
            except TypeError as error:
                raise ValueError(
                    f"filename entry at family row {row} must be a path or collection of paths."
                ) from error
        full_paths.append(family_paths)
        labels.append(", ".join(Path(filename).name for filename in family_paths))
    return labels, full_paths


def plot_family_avg(
    stats: "FamilyAvg", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x: str = "Family", plf: bool = False,
) -> go.Figure:
    """Plot stored family-average channel values without recalculation.

    Parameters
    ----------
    stats : FamilyAvg
        Stored family-average statistics and row-aligned metadata.
    channel : str
        Exact y-axis channel name, including units.
    statistic : {"mean", "std", "min", "max"}
        Stored statistic used for both numeric axes.
    x : str, default "Family"
        ``Family`` or an exact numeric channel in the selected table.
    plf : bool, default False
        Select the PLF-adjusted statistic table when True.

    Returns
    -------
    plotly.graph_objects.Figure
        Marker-only family exploration figure without displaying it.

    Examples
    --------
    >>> fig = plot_family_avg(
    ...     family_stats, channel="TowerMx_[kNm]", statistic="max", x="Family"
    ... )
    """
    table = _selected_table(stats, statistic, plf)
    families = _family_values(stats, table)
    y_values = _numeric_values(table, channel, "y")
    if not isinstance(x, str):
        raise ValueError("x must be 'Family' or an exact channel name.")
    x_values = families if x == "Family" else _numeric_values(table, x, "x")
    filename_labels, full_paths = _filename_metadata(stats, len(table))
    plf_label = "yes" if plf else "no"
    customdata = [
        [families[row], filename_labels[row], channel, statistic, plf_label, full_paths[row]]
        for row in range(len(table))
    ]

    figure = go.Figure()
    figure.add_scatter(
        x=x_values,
        y=y_values,
        mode="markers",
        name="Families",
        marker={"color": "#636EFA", "opacity": 0.7, "size": 8},
        customdata=customdata,
        hovertemplate=(
            "Family: %{customdata[0]}<br>Value: %{y}<br>Channel: %{customdata[2]}"
            "<br>Statistic: %{customdata[3]}<br>PLF adjusted: %{customdata[4]}"
            "<br>Files: %{customdata[1]}<extra></extra>"
        ),
    )
    mode_label = "PLF-adjusted" if plf else "raw"
    x_title = "Family" if x == "Family" else f"{statistic}: {x}"
    figure.update_layout(
        title=f"{statistic}: {channel} ({mode_label})",
        xaxis_title=x_title,
        yaxis_title=f"{statistic}: {channel}",
        template="plotly_white",
        legend={"groupclick": "toggleitem"},
    )
    return figure
