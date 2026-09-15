"""Interactive exploration of stored family-average statistics."""

from math import isfinite
from numbers import Real
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
import plotly.graph_objects as go

from load_arena.visualization.common import PlotSeries, plot


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


def _plot_provenance(
    stats: "FamilyAvg",
    table: pd.DataFrame,
    families: list,
    channel: str,
    statistic: str,
    plf: bool,
) -> tuple[
    list[str], list[list[str]], list[str], list[int], list[list[str]], list[str | None]
]:
    """Select family summaries and full-path metadata for plotted points.

    Parameters
    ----------
    stats : FamilyAvg
        Stored result with optional long-form provenance.
    table : pandas.DataFrame
        Selected statistic table used by the plot.
    families : list
        Family identifiers in plotted row order.
    channel : str
        Exact plotted y-axis channel.
    statistic : str
        Selected statistic name.
    plf : bool
        Whether the selected table is PLF-adjusted.

    Returns
    -------
    tuple
        Basename labels, full member paths, methods, member counts, full
        contributing paths, and exact source paths in family row order.

    Examples
    --------
    >>> metadata = _plot_provenance(
    ...     family_stats, family_stats.max, [1], "Load", "max", False,
    ... )
    """
    fallback_labels, fallback_paths = _filename_metadata(stats, len(table))
    channel_position = [column for column in table.columns if column != "Family"].index(
        channel
    )
    required = {
        "Family", "statistic", "plf_adjusted", "channel_position",
        "averaging_method", "member_count", "member_files", "contributing_files",
    }
    if stats.provenance.empty or not required.issubset(stats.provenance.columns):
        return (
            fallback_labels,
            fallback_paths,
            ["unknown"] * len(table),
            [len(paths) for paths in fallback_paths],
            fallback_paths,
            [None] * len(table),
        )

    labels = []
    full_paths = []
    methods = []
    member_counts = []
    contributing_paths = []
    source_files = []
    for row, family in enumerate(families):
        matches = stats.provenance.loc[
            (stats.provenance["Family"] == family)
            & (stats.provenance["statistic"] == statistic)
            & (stats.provenance["plf_adjusted"] == plf)
            & (stats.provenance["channel_position"] == channel_position)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one provenance record for family {family!r}, "
                f"statistic {statistic!r}, channel {channel!r}."
            )
        record = matches.iloc[0]
        paths = [str(filename) for filename in record["member_files"]]
        contributors = [str(filename) for filename in record["contributing_files"]]
        full_paths.append(paths)
        contributing_paths.append(contributors)
        labels.append(", ".join(Path(filename).name for filename in paths))
        methods.append(str(record["averaging_method"]))
        member_counts.append(int(record["member_count"]))
        source_file = record.get("source_file")
        source_files.append(None if pd.isna(source_file) else str(source_file))
    return (
        labels, full_paths, methods, member_counts, contributing_paths, source_files,
    )


def family_avg_series(
    stats: "FamilyAvg", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x_channel: str | None = None,
    x_statistic: Literal["mean", "std", "min", "max"] = "mean",
    plf: bool = False, x_plf: bool | None = None, name: str = "Families",
) -> PlotSeries:
    """Convert stored family-average values into a common plotting series.

    Parameters
    ----------
    stats : FamilyAvg
        Stored family-average statistics and row-aligned metadata.
    channel : str
        Exact y-axis channel name, including units.
    statistic : {"mean", "std", "min", "max"}
        Stored statistic used for the y-axis.
    x_channel : str or None, default None
        Exact numeric x-axis channel; None uses stored family labels.
    x_statistic : {"mean", "std", "min", "max"}, default "mean"
        Stored statistic for x_channel; unused when x_channel is None.
    plf : bool, default False
        Select the PLF-adjusted y-axis table when True.
    x_plf : bool or None, default None
        Select the PLF-adjusted x-axis table when True or the raw table when
        False. None follows plf. Unused when x_channel is None.
    name : str, default "Families"
        Legend label for the resulting series.

    Returns
    -------
    PlotSeries
        Stored family values with member and provenance metadata.

    Examples
    --------
    >>> series = family_avg_series(
    ...     family_stats, channel="TowerMx_[kNm]", statistic="max",
    ...     x_channel="WindSpeed_[m/s]", x_statistic="mean",
    ... )
    """
    y_table = _selected_table(stats, statistic, plf)
    families = _family_values(stats, y_table)
    y_values = _numeric_values(y_table, channel, "y")
    if x_channel is None:
        x_values = families
        effective_x_plf = None
    else:
        if not isinstance(x_channel, str):
            raise ValueError("x_channel must be None or an exact channel name.")
        effective_x_plf = plf if x_plf is None else x_plf
        x_table = _selected_table(stats, x_statistic, effective_x_plf)
        _family_values(stats, x_table)
        x_values = _numeric_values(x_table, x_channel, "x")
    (
        filename_labels,
        full_paths,
        methods,
        member_counts,
        contributing_paths,
        source_files,
    ) = (
        _plot_provenance(stats, y_table, families, channel, statistic, plf)
    )
    plf_label = "yes" if plf else "no"
    metadata_x_channel = "Family" if x_channel is None else x_channel
    metadata_x_statistic = None if x_channel is None else x_statistic
    metadata_x_plf = (
        None if effective_x_plf is None else ("yes" if effective_x_plf else "no")
    )
    customdata = [
        [
            families[row], filename_labels[row], channel, statistic, plf_label,
            full_paths[row], methods[row], member_counts[row], contributing_paths[row],
            source_files[row], metadata_x_channel, metadata_x_statistic, metadata_x_plf,
        ]
        for row in range(len(y_table))
    ]
    mode_label = "PLF-adjusted" if plf else "raw"
    if x_channel is None:
        x_title = "Family"
        x_hover = ""
    else:
        x_mode_label = "PLF-adjusted" if effective_x_plf else "raw"
        x_title = f"{x_statistic}: {x_channel} ({x_mode_label})"
        x_hover = (
            "<br>X value: %{x}<br>X channel: %{customdata[10]}"
            "<br>X statistic: %{customdata[11]}"
            "<br>X PLF adjusted: %{customdata[12]}"
        )
    return PlotSeries(
        x=x_values,
        y=y_values,
        name=name,
        x_label=x_title,
        y_label=f"{statistic}: {channel}",
        title=f"{statistic}: {channel} ({mode_label})",
        metadata=customdata,
        hovertemplate=(
            "Series: %{fullData.name}<br>Family: %{customdata[0]}"
            "<br>Value: %{y}<br>Channel: %{customdata[2]}"
            "<br>Statistic: %{customdata[3]}<br>PLF adjusted: %{customdata[4]}"
            "<br>Averaging method: %{customdata[6]}"
            "<br>Member count: %{customdata[7]}<br>Files: %{customdata[1]}"
            f"{x_hover}<extra></extra>"
        ),
        x_kind="categorical" if x_channel is None else "numeric",
    )


def plot_family_avg(
    stats: "FamilyAvg", *, channel: str,
    statistic: Literal["mean", "std", "min", "max"],
    x_channel: str | None = None,
    x_statistic: Literal["mean", "std", "min", "max"] = "mean",
    plf: bool = False, x_plf: bool | None = None,
    kind: Literal["scatter", "bar", "line"] = "scatter",
) -> go.Figure:
    """Plot stored family-average values through the common plotting layer.

    Parameters
    ----------
    stats : FamilyAvg
        Stored family-average statistics and row-aligned metadata.
    channel : str
        Exact y-axis channel name, including units.
    statistic : {"mean", "std", "min", "max"}
        Stored statistic used for the y-axis.
    x_channel : str or None, default None
        Exact numeric x-axis channel; None uses stored family labels.
    x_statistic : {"mean", "std", "min", "max"}, default "mean"
        Stored statistic for x_channel; unused when x_channel is None.
    plf : bool, default False
        Select the PLF-adjusted y-axis table when True.
    x_plf : bool or None, default None
        Select the PLF-adjusted x-axis table when True or the raw table when
        False. None follows plf. Unused when x_channel is None.
    kind : {"scatter", "bar", "line"}, default "scatter"
        Plot type forwarded to the common plotting layer.

    Returns
    -------
    plotly.graph_objects.Figure
        Marker-only family figure returned without display or recalculation.

    Examples
    --------
    >>> fig = plot_family_avg(
    ...     family_stats, channel="TowerMx_[kNm]", statistic="max",
    ...     x_channel="WindSpeed_[m/s]", kind="bar",
    ... )
    """
    series = family_avg_series(
        stats,
        channel=channel,
        statistic=statistic,
        x_channel=x_channel,
        x_statistic=x_statistic,
        plf=plf,
        x_plf=x_plf,
    )
    return plot(series, kind=kind)
