"""Interactive exploration of raw per-simulation statistics."""

from math import isfinite
from numbers import Real
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go


if TYPE_CHECKING:
    from load_arena.process.concatenate_stats import All_stats


def plot_statistics(
    stats: "All_stats", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
) -> go.Figure:
    """Build an interactive plot of stored simulation values without displaying.

    Parameters
    ----------
    stats : All_stats
        Raw statistics and the existing positional filename list.
    channel : str
        Exact, unambiguous column name in the selected statistics table.
    statistic : {"mean", "std", "min", "max"}
        Raw per-simulation statistic to display.

    Returns
    -------
    plotly.graph_objects.Figure
        Simulation values plotted by zero-based row position. Invalid data raises
        ValueError; source tables are never modified and rows are never dropped.

    Examples
    --------
    >>> fig = plot_statistics(stats, channel="Aerot._[kW]", statistic="max")
    """
    if not isinstance(statistic, str) or statistic not in ("mean", "std", "min", "max"):
        raise ValueError("statistic must be one of: mean, std, min, max.")
    table = getattr(stats, statistic)
    if not isinstance(table, pd.DataFrame):
        raise ValueError(f"stats.{statistic} must be a pandas DataFrame.")
    if not isinstance(channel, str) or list(table.columns).count(channel) != 1:
        raise ValueError(
            f"channel must identify exactly one column in stats.{statistic}; "
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
                f"{statistic} for channel {channel!r} at simulation row {row} "
                "must be a finite numeric value."
            )
    figure = go.Figure()
    figure.add_scatter(
        x=list(range(count)), y=values, mode="markers", name="Simulations",
        marker={"color": "#636EFA", "opacity": 0.7, "size": 8},
        customdata=[[str(filename)] for filename in stats.filename],
        hovertemplate="Simulation row: %{x}<br>File: %{customdata[0]}"
        "<br>Value: %{y}<extra></extra>",
    )
    figure.update_layout(
        title=f"{statistic}: {channel}", xaxis_title="Simulation row (zero-based)",
        yaxis_title=f"{statistic}: {channel}", template="plotly_white",
        legend={"groupclick": "toggleitem"},
    )
    return figure
