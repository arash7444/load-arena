"""Interactive exploration of raw per-simulation statistics."""

from math import isfinite
from numbers import Real
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go

from load_arena.visualization.common import PlotSeries, plot


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


def statistics_series(
    stats: "All_stats", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x_channel: str | None = None,
    x_statistic: Literal["mean", "std", "min", "max"] = "mean",
    name: str = "Simulations",
) -> PlotSeries:
    """Convert stored simulation statistics into a common plotting series.

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
    name : str, default "Simulations"
        Legend label for the resulting series.

    Returns
    -------
    PlotSeries
        Stored values and row-level filename metadata without recalculation.

    Examples
    --------
    >>> series = statistics_series(
    ...     stats, channel="TowerMy_[kNm]", statistic="max",
    ...     x_channel="WSPgl._[m/s]", x_statistic="mean",
    ... )
    """
    values = _selected_values(stats, channel, statistic, "y")
    x_values = (list(range(len(values))) if x_channel is None
                else _selected_values(stats, x_channel, x_statistic, "x"))
    x_title = "Simulation row (zero-based)" if x_channel is None else f"{x_statistic}: {x_channel}"
    metadata = [
        [
            Path(str(stats.filename[row])).name,
            row,
            str(stats.filename[row]),
            channel,
            statistic,
            x_channel,
            x_statistic if x_channel is not None else None,
        ]
        for row in range(len(values))
    ]
    return PlotSeries(
        x=x_values,
        y=values,
        name=name,
        x_label=x_title,
        y_label=f"{statistic}: {channel}",
        title=f"{statistic}: {channel}",
        metadata=metadata,
        hovertemplate=(
            "Series: %{fullData.name}<br>Simulation row: %{customdata[1]}"
            "<br>File: %{customdata[0]}<br>Channel: %{customdata[3]}"
            "<br>Statistic: %{customdata[4]}<br>X: %{x}<br>Y: %{y}<extra></extra>"
        ),
        x_kind="numeric",
    )


def plot_statistics(
    stats: "All_stats", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x_channel: str | None = None,
    x_statistic: Literal["mean", "std", "min", "max"] = "mean",
    kind: Literal["scatter", "bar", "line"] = "scatter",
) -> go.Figure:
    """Plot stored simulation statistics through the common plotting layer.

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
        Plot type applied to the extracted series.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive figure without display, recalculation, or source mutation.

    Examples
    --------
    >>> fig = plot_statistics(stats, channel="TowerMy_[kNm]", statistic="max")
    """
    series = statistics_series(
        stats,
        channel=channel,
        statistic=statistic,
        x_channel=x_channel,
        x_statistic=x_statistic,
    )
    return plot(series, kind=kind)
