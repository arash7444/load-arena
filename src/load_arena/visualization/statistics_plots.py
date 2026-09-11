"""Interactive exploration of raw per-simulation statistics."""

from math import isfinite
from numbers import Real
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go


if TYPE_CHECKING:
    from load_arena.process.concatenate_stats import All_stats


def _selected_values(stats: "All_stats", channel: str, statistic: str, axis: str) -> list:
    """Validate and extract one axis in simulation row order.

    Parameters
    ----------
    stats : All_stats
        Stored statistics result.
    channel : str
        Exact, unambiguous column name in the selected statistics table.
    statistic : str
        Raw statistic name.
    axis : str
        Axis label for actionable validation errors.

    Returns
    -------
    list
        Finite numeric values aligned with the existing filename list.

    Examples
    --------
    >>> values = _selected_values(stats, "Aerot._[kW]", "max", "y")
    """
    if not isinstance(statistic, str) or statistic not in ("mean", "std", "min", "max"):
        raise ValueError(f"{axis}-axis statistic must be one of: mean, std, min, max.")
    table = getattr(stats, statistic)
    if not isinstance(table, pd.DataFrame):
        raise ValueError(f"stats.{statistic} must be a pandas DataFrame.")
    if not isinstance(channel, str) or list(table.columns).count(channel) != 1:
        raise ValueError(
            f"{axis}-axis channel must identify exactly one column in stats.{statistic}; "
            f"received {channel!r}. Available columns: {list(table.columns)!r}"
        )
    count = len(table)
    if count == 0:
        raise ValueError("Statistics exploration requires at least one simulation.")
    if len(stats.filename) != count:
        raise ValueError(f"filename must contain one entry per simulation ({count} entries).")
    values = table[channel].tolist()
    for row, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError(
                f"{axis}-axis {statistic} for channel {channel!r} at simulation row {row} "
                "must be a finite numeric value."
            )
    return values


def plot_statistics(
    stats: "All_stats", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x_channel: str | None = None,
    x_statistic: Literal["mean", "std", "min", "max"] = "mean",
    kind: Literal["scatter", "bar", "line"] = "scatter",
) -> go.Figure:
    """Plot two stored channel statistics paired by simulation row position.

    Parameters
    ----------
    stats : All_stats
        Raw statistics and their existing positional filename list.
    channel : str
        Exact y-axis channel name, including units.
    statistic : {"mean", "std", "min", "max"}
        Raw statistic for the y-axis.
    x_channel : str or None, default None
        Exact x-axis channel name; None uses zero-based simulation positions.
    x_statistic : {"mean", "std", "min", "max"}, default "mean"
        Raw x-axis statistic; unused when x_channel is None.
    kind : {"scatter", "bar", "line"}, default "scatter"
        Plot type. Lines use ascending x order, preserving ties in input order.
        No aggregation or family grouping is performed.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive figure without display, recalculation, or source mutation.
        Invalid selections or nonfinite values raise ValueError.

    Examples
    --------
    >>> fig = plot_statistics(stats, channel="TowerMy_[kNm]", statistic="max",
    ...                       x_channel="WSPgl._[m/s]", x_statistic="mean")
    """
    if not isinstance(kind, str) or kind not in ("scatter", "bar", "line"):
        raise ValueError("kind must be one of: scatter, bar, line.")
    values = _selected_values(stats, channel, statistic, "y")
    x_values = (list(range(len(values))) if x_channel is None
                else _selected_values(stats, x_channel, x_statistic, "x"))
    x_title = "Simulation row (zero-based)" if x_channel is None else f"{x_statistic}: {x_channel}"
    rows = list(range(len(values)))
    if kind == "line":
        rows.sort(key=lambda row: x_values[row])
    trace_data = dict(
        x=[x_values[row] for row in rows], y=[values[row] for row in rows], name="Simulations",
        customdata=[
            [Path(str(stats.filename[row])).name, row, str(stats.filename[row])]
            for row in rows
        ],
        hovertemplate="Simulation row: %{customdata[1]}<br>File: %{customdata[0]}"
        "<br>X: %{x}<br>Y: %{y}<extra></extra>",
    )
    figure = go.Figure()
    if kind == "bar":
        figure.add_bar(**trace_data, marker={"color": "#636EFA"})
    else:
        figure.add_scatter(
            **trace_data, mode="markers" if kind == "scatter" else "lines+markers",
            marker={"color": "#636EFA", "opacity": 0.7, "size": 8},
        )
    figure.update_layout(
        title=f"{statistic}: {channel}", xaxis_title=x_title,
        yaxis_title=f"{statistic}: {channel}", template="plotly_white",
        legend={"groupclick": "toggleitem"},
    )
    return figure
