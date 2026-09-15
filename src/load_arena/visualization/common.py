"""Common Plotly series and figure construction for LoadArena results."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Any, Literal, Sequence

import plotly.graph_objects as go


@dataclass(frozen=True)
class PlotSeries:
    """Describe one result trace without coupling plotting to its source type.

    Parameters
    ----------
    x, y : sequence
        Row-aligned axis values. Y values must be finite numbers.
    name : str
        Legend label for the trace.
    x_label, y_label : str
        Descriptions used when all plotted series share an axis meaning.
    title : str
        Preferred title when all plotted series share the same result title.
    metadata : sequence
        Row-aligned Plotly custom data containing result-specific provenance.
    hovertemplate : str
        Plotly hover template interpreting the result-specific metadata.
    x_kind : {"numeric", "categorical"}
        Controls whether a line trace is numerically sorted or keeps input order.

    Returns
    -------
    PlotSeries
        Validated, immutable trace data with tuple-backed row collections.

    Examples
    --------
    >>> series = PlotSeries(
    ...     x=(4.0, 8.0), y=(10.0, 20.0), name="Example",
    ...     x_label="Wind speed", y_label="Load", title="Mean load",
    ...     metadata=(("case_1.int",), ("case_2.int",)),
    ...     hovertemplate="File: %{customdata[0]}<br>Y: %{y}<extra></extra>",
    ...     x_kind="numeric",
    ... )
    """

    x: Sequence[Any]
    y: Sequence[Real]
    name: str
    x_label: str
    y_label: str
    title: str
    metadata: Sequence[Any]
    hovertemplate: str
    x_kind: Literal["numeric", "categorical"]

    def __post_init__(self) -> None:
        """Normalize row collections and reject structurally malformed series.

        Parameters
        ----------
        None

        Returns
        -------
        None
            The frozen instance is normalized in place during initialization.

        Examples
        --------
        >>> PlotSeries(
        ...     x=[1], y=[2], name="A", x_label="X", y_label="Y", title="Y",
        ...     metadata=[["case.int"]], hovertemplate="%{y}", x_kind="numeric",
        ... ).x
        (1,)
        """
        try:
            x_values = tuple(self.x)
            y_values = tuple(self.y)
            metadata = tuple(self.metadata)
        except TypeError as error:
            raise ValueError("x, y, and metadata must be finite sequences.") from error
        if not x_values:
            raise ValueError("PlotSeries requires at least one point.")
        if len(x_values) != len(y_values) or len(x_values) != len(metadata):
            raise ValueError("x, y, and metadata must contain the same number of points.")
        for field_name in ("name", "x_label", "y_label", "title", "hovertemplate"):
            if not isinstance(getattr(self, field_name), str):
                raise ValueError(f"{field_name} must be a string.")
        if self.x_kind not in ("numeric", "categorical"):
            raise ValueError("x_kind must be either 'numeric' or 'categorical'.")
        for row, value in enumerate(y_values):
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise ValueError(f"y value at row {row} must be a finite number.")
        if self.x_kind == "numeric":
            for row, value in enumerate(x_values):
                if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                    raise ValueError(f"numeric x value at row {row} must be a finite number.")
        object.__setattr__(self, "x", x_values)
        object.__setattr__(self, "y", y_values)
        object.__setattr__(self, "metadata", metadata)


def _common_label(series: tuple[PlotSeries, ...], attribute: str, neutral: str) -> str:
    """Return a shared series label or a neutral label when meanings differ.

    Parameters
    ----------
    series : tuple of PlotSeries
        Series participating in one figure.
    attribute : str
        PlotSeries text attribute to compare.
    neutral : str
        Label used when the values are not identical.

    Returns
    -------
    str
        Shared value or the supplied neutral value.

    Examples
    --------
    >>> _common_label((series,), "y_label", "Y") == series.y_label
    True
    """
    values = {getattr(item, attribute) for item in series}
    return values.pop() if len(values) == 1 else neutral


def plot(
    *series: PlotSeries,
    kind: Literal["scatter", "bar", "line"] = "scatter",
) -> go.Figure:
    """Plot one or more result-independent series in a shared Plotly figure.

    Parameters
    ----------
    *series : PlotSeries
        Validated traces to add in argument order.
    kind : {"scatter", "bar", "line"}, default "scatter"
        Trace type applied to every series. Numeric line x-values are sorted;
        categorical line x-values retain their input order.

    Returns
    -------
    plotly.graph_objects.Figure
        Combined figure that is returned without being displayed.

    Examples
    --------
    >>> figure = plot(simulation_series, family_series, kind="scatter")
    """
    if not series:
        raise ValueError("plot requires at least one PlotSeries.")
    if any(not isinstance(item, PlotSeries) for item in series):
        raise ValueError("plot accepts only PlotSeries objects.")
    if not isinstance(kind, str) or kind not in ("scatter", "bar", "line"):
        raise ValueError("kind must be one of: scatter, bar, line.")

    figure = go.Figure()
    for item in series:
        rows = list(range(len(item.x)))
        if kind == "line" and item.x_kind == "numeric":
            rows.sort(key=lambda row: item.x[row])
        trace_data = {
            "x": [item.x[row] for row in rows],
            "y": [item.y[row] for row in rows],
            "name": item.name,
            "customdata": [item.metadata[row] for row in rows],
            "hovertemplate": item.hovertemplate,
        }
        if kind == "bar":
            figure.add_bar(**trace_data)
        else:
            figure.add_scatter(
                **trace_data,
                mode="markers" if kind == "scatter" else "lines+markers",
                marker={"opacity": 0.7, "size": 8},
            )
    figure.update_layout(
        title=_common_label(series, "title", "Y"),
        xaxis_title=_common_label(series, "x_label", "X"),
        yaxis_title=_common_label(series, "y_label", "Y"),
        template="plotly_white",
        legend={"groupclick": "toggleitem"},
    )
    return figure
