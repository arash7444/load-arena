"""Interactive exploration of raw per-simulation statistics."""

from math import isfinite
from numbers import Real
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

from load_arena.process.concatenate_stats import _validate_statistics_metadata

if TYPE_CHECKING:
    from load_arena.process.concatenate_stats import All_stats


def plot_statistics(
    stats: "All_stats", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
) -> go.Figure:
    """Build simulation and arithmetic family-average traces without displaying.

    Parameters
    ----------
    stats : All_stats
        Raw statistics with positional filename, dlc, and wind_speed lists.
    channel : str
        Exact, unambiguous column name in the selected statistics table.
    statistic : {"mean", "std", "min", "max"}
        Per-simulation statistic; families use exact DLC and nominal speed pairs.

    Returns
    -------
    plotly.graph_objects.Figure
        One simulation trace and one average trace per DLC. Invalid data raises
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
    labels, speeds = _validate_statistics_metadata(count, stats.dlc, stats.wind_speed)
    if len(stats.filename) != count:
        raise ValueError(f"filename must contain one entry per simulation ({count} entries).")
    values = table[channel].tolist()
    for row, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError(
                f"{statistic} for channel {channel!r} at simulation row {row} "
                "must be a finite numeric value."
            )
    selected = pd.DataFrame({
        "simulation_row": range(count), "filename": list(stats.filename),
        "dlc": labels, "wind_speed": speeds, "value": values,
    })
    figure = go.Figure()
    for index, (label, simulations) in enumerate(selected.groupby("dlc", sort=False)):
        color = qualitative.Plotly[index % len(qualitative.Plotly)]
        averages = simulations.groupby("wind_speed", sort=True)["value"].agg(["mean", "size"]).reset_index()
        figure.add_scatter(
            x=simulations["wind_speed"].tolist(), y=simulations["value"].tolist(),
            mode="markers", name=f"{label}: simulations", legendgroup=label,
            marker={"color": color, "opacity": 0.6, "size": 8},
            customdata=simulations[["simulation_row", "filename", "dlc"]].values.tolist(),
            hovertemplate="Row: %{customdata[0]}<br>File: %{customdata[1]}"
            "<br>DLC: %{customdata[2]}<br>Wind speed: %{x} m/s<br>Value: %{y}<extra></extra>",
        )
        figure.add_scatter(
            x=averages["wind_speed"].tolist(), y=averages["mean"].tolist(),
            mode="lines+markers", name=f"{label}: family average", legendgroup=label,
            line={"color": color, "width": 2}, marker={"color": color, "size": 10, "symbol": "diamond"},
            customdata=[[label, int(size)] for size in averages["size"]],
            hovertemplate="DLC: %{customdata[0]}<br>Wind speed: %{x} m/s"
            "<br>Family size: %{customdata[1]}<br>Average: %{y}<extra></extra>",
        )
    figure.update_layout(
        title=f"{statistic}: {channel}", xaxis_title="Nominal wind speed [m/s]",
        yaxis_title=f"{statistic}: {channel}", template="plotly_white",
        legend={"groupclick": "toggleitem"},
    )
    return figure
