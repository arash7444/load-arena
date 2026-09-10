"""Contracts for statistics-only exploration without reading simulation files."""

import copy
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

from load_arena.process.concatenate_stats import All_stats


@pytest.fixture
def stats():
    """Create statistics with repeated paths and nondefault row indices.

    Parameters
    ----------
    None

    Returns
    -------
    All_stats
        Synthetic statistics with distinct values for each statistic.

    Examples
    --------
    >>> result = stats.__wrapped__()
    """
    tables = {
        name: pd.DataFrame({"load_[kN]": [20 + offset, 2 + offset, 6 + offset, 100 + offset]}, index=[9, 2, 8, 1])
        for offset, name in enumerate(("mean", "std", "min", "max"))
    }
    return All_stats(
        **tables, **{f"{name}_plf": table * 10 for name, table in tables.items()},
        filename=["repeat.int", "repeat.int", "third.int", "fourth.int"], family=["NaN"] * 4,
    )


@pytest.mark.parametrize("statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)])
def test_values_and_immutable_results(stats, statistic, offset, monkeypatch):
    """Check raw values, positional identity, and no recalculation.

    Parameters
    ----------
    stats : All_stats
        Synthetic result fixture.
    statistic : str
        Selected statistic.
    offset : int
        Expected synthetic value offset.
    monkeypatch : pytest.MonkeyPatch
        Fixture replacing calculation with a failure sentinel.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py
    """
    before = copy.deepcopy(stats)
    module = importlib.import_module("load_arena.process.concatenate_stats")
    monkeypatch.setattr(module, "concatenate_stats", lambda *args, **kwargs: pytest.fail("recalculation"))
    monkeypatch.setattr(module, "ReadHawc2", lambda *args, **kwargs: pytest.fail("simulation read"))
    figure = stats.explore(channel="load_[kN]", statistic=statistic, show=False)
    assert len(figure.data) == 1
    individual = figure.data[0]
    assert list(individual.x) == [0, 1, 2, 3]
    assert list(individual.y) == [20 + offset, 2 + offset, 6 + offset, 100 + offset]
    assert individual.customdata[0][0] == individual.customdata[1][0] == "repeat.int"
    assert individual.mode == "markers"
    assert "File:" in individual.hovertemplate
    assert "load_[kN]" in figure.layout.yaxis.title.text
    assert figure.layout.xaxis.title.text == "Simulation row (zero-based)"
    for name, value in vars(before).items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(getattr(stats, name), value)
        else:
            assert getattr(stats, name) == value


@pytest.mark.parametrize("field,value,match", [
    ("filename", ["one.int"], "filename"),
])
def test_invalid_metadata(stats, field, value, match):
    """Reject invalid metadata rather than silently discarding simulation rows.

    Parameters
    ----------
    stats : All_stats
        Result fixture.
    field : str
        Metadata field to replace.
    value : object
        Invalid metadata.
    match : str
        Expected error text.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k invalid_metadata
    """
    setattr(stats, field, value)
    with pytest.raises(ValueError, match=match):
        stats.explore(channel="load_[kN]", statistic="mean", show=False)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "invalid", None, True])
def test_invalid_values(stats, value):
    """Reject nonfinite or nonnumeric selected values with a row-specific error.

    Parameters
    ----------
    stats : All_stats
        Result fixture.
    value : object
        Invalid selected value.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k invalid_values
    """
    stats.mean = stats.mean.astype(object)
    stats.mean.iloc[1, 0] = value
    with pytest.raises(ValueError, match="row 1"):
        stats.explore(channel="load_[kN]", statistic="mean", show=False)


def test_invalid_selection_and_empty_results(stats):
    """Reject unsupported statistics, missing or duplicate columns, and no rows.

    Parameters
    ----------
    stats : All_stats
        Result fixture.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k invalid_selection
    """
    with pytest.raises(ValueError, match="statistic"):
        stats.explore(channel="load_[kN]", statistic="mean_plf", show=False)
    with pytest.raises(ValueError, match="exactly one"):
        stats.explore(channel="missing", statistic="mean", show=False)
    stats.mean = pd.concat([stats.mean, stats.mean], axis=1)
    with pytest.raises(ValueError, match="exactly one"):
        stats.explore(channel="load_[kN]", statistic="mean", show=False)
    stats.mean = pd.DataFrame(columns=["load_[kN]"])
    with pytest.raises(ValueError, match="at least one"):
        stats.explore(channel="load_[kN]", statistic="mean", show=False)


def test_display_and_legacy_construction(stats, monkeypatch):
    """Display once by default and preserve construction without new metadata.

    Parameters
    ----------
    stats : All_stats
        Result fixture.
    monkeypatch : pytest.MonkeyPatch
        Fixture intercepting Plotly display.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k display
    """
    displayed = []
    monkeypatch.setattr(go.Figure, "show", lambda self: displayed.append(self))
    figure = stats.explore(channel="load_[kN]", statistic="mean")
    assert displayed == [figure]
    assert isinstance(stats.explore(channel="load_[kN]", statistic="mean", show=False), go.Figure)
    assert displayed == [figure]
    legacy = All_stats(**vars(stats))
    assert isinstance(legacy.explore(channel="load_[kN]", statistic="mean", show=False), go.Figure)


def test_visualization_import_without_ai_credentials():
    """Import plotting in a fresh process without loading the AI integration.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k credentials
    """
    environment = dict(os.environ)
    environment.pop("GEMINI_API_KEY", None)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; import load_arena.visualization; "
         "from load_arena.visualization.statistics_plots import plot_statistics; "
         "assert 'load_arena.AI.AI_tool_calling_V3' not in sys.modules"],
        env=environment, capture_output=True, text=True, timeout=60,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("kind", ["scatter", "bar", "line"])
@pytest.mark.parametrize("x_statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)])
def test_channel_axes_and_plot_types(stats, kind, x_statistic, offset):
    """Pair independent statistics positionally and sort only line plots.

    Parameters
    ----------
    stats : All_stats
        Synthetic result fixture.
    kind : str
        Plot type under test.
    x_statistic : str
        Selected x statistic.
    offset : int
        Expected x value offset.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k channel_axes
    """
    table = getattr(stats, x_statistic)
    table["wind_[m/s]"] = [12 + offset, 8 + offset, 8 + offset, 4 + offset]
    table.index = [40, 10, 90, 20]
    before = copy.deepcopy(stats)
    figure = stats.explore(
        channel="load_[kN]", statistic="max", x_channel="wind_[m/s]",
        x_statistic=x_statistic, kind=kind, show=False,
    )
    trace = figure.data[0]
    order = [3, 1, 2, 0] if kind == "line" else [0, 1, 2, 3]
    assert list(trace.x) == [[12 + offset, 8 + offset, 8 + offset, 4 + offset][i] for i in order]
    assert list(trace.y) == [[23, 5, 9, 103][i] for i in order]
    assert [row[1] for row in trace.customdata] == order
    assert [row[0] for row in trace.customdata] == [stats.filename[i] for i in order]
    assert trace.type == ("bar" if kind == "bar" else "scatter")
    if kind != "bar":
        assert trace.mode == ("lines+markers" if kind == "line" else "markers")
    assert figure.layout.xaxis.title.text == f"{x_statistic}: wind_[m/s]"
    assert figure.layout.yaxis.title.text == "max: load_[kN]"
    for name in ("mean", "std", "min", "max"):
        pd.testing.assert_frame_equal(getattr(stats, name), getattr(before, name))


@pytest.mark.parametrize("failure", ["channel", "duplicate", "statistic", "length", "nan", "kind"])
def test_invalid_x_axis_and_kind(stats, failure):
    """Reject invalid x selections and mismatched rows without silent alignment.

    Parameters
    ----------
    stats : All_stats
        Synthetic result fixture.
    failure : str
        Invalid input scenario.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k invalid_x
    """
    kwargs = dict(channel="load_[kN]", statistic="max", x_channel="load_[kN]", show=False)
    if failure == "channel":
        kwargs["x_channel"] = "missing"
    elif failure == "duplicate":
        stats.mean = pd.concat([stats.mean, stats.mean], axis=1)
    elif failure == "statistic":
        kwargs["x_statistic"] = "median"
    elif failure == "length":
        stats.mean = stats.mean.iloc[:-1]
    elif failure == "nan":
        stats.mean = stats.mean.astype(float)
        stats.mean.iloc[1, 0] = float("nan")
    else:
        kwargs["kind"] = "pie"
    with pytest.raises(ValueError):
        stats.explore(**kwargs)
