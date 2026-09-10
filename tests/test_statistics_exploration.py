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

from load_arena import calculate_statistics
from load_arena.process.concatenate_stats import All_stats


@pytest.fixture
def stats():
    """Create unsorted families with repeated paths and nondefault row indices.

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
        dlc=["DLC12", "DLC12", "DLC12", "DLC13"], wind_speed=[12, 8, 8, 8],
    )


@pytest.mark.parametrize("statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)])
def test_grouping_and_immutable_results(stats, statistic, offset, monkeypatch):
    """Check raw values, positional identity, sorted families, and no recalculation.

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
    assert len(figure.data) == 4
    individual, average, other, other_average = figure.data
    assert list(individual.x) == [12, 8, 8]
    assert list(individual.y) == [20 + offset, 2 + offset, 6 + offset]
    assert list(average.x) == [8, 12]
    assert list(average.y) == [4 + offset, 20 + offset]
    assert list(other_average.y) == [100 + offset]
    assert list(other.x) == [8]
    assert individual.customdata[0][1] == individual.customdata[1][1] == "repeat.int"
    assert [row[0] for row in individual.customdata] == [0, 1, 2]
    assert [row[1] for row in average.customdata] == [2, 1]
    assert individual.marker.color == average.line.color != other_average.line.color
    assert average.mode == "lines+markers"
    assert "Family size" in average.hovertemplate
    assert "File:" in individual.hovertemplate
    assert "load_[kN]" in figure.layout.yaxis.title.text
    for name, value in vars(before).items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(getattr(stats, name), value)
        else:
            assert getattr(stats, name) == value


@pytest.mark.parametrize("field,value,match", [
    ("dlc", None, "dlc"), ("dlc", ["DLC12"], "dlc"),
    ("dlc", ["DLC12", " ", "DLC12", "DLC13"], "row 1"),
    ("wind_speed", None, "wind_speed"), ("wind_speed", [8], "wind_speed"),
    ("wind_speed", [8, float("nan"), 8, 8], "row 1"),
    ("wind_speed", [8, float("inf"), 8, 8], "row 1"),
    ("wind_speed", [8, -1, 8, 8], "row 1"),
    ("wind_speed", [8, "8", 8, 8], "row 1"),
    ("wind_speed", [8, True, 8, 8], "row 1"),
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
    legacy = All_stats(**{name: value for name, value in vars(stats).items() if name not in ("dlc", "wind_speed")})
    assert legacy.dlc is legacy.wind_speed is None
    with pytest.raises(ValueError, match="dlc"):
        legacy.explore(channel="load_[kN]", statistic="mean", show=False)
    legacy.dlc, legacy.wind_speed = stats.dlc, stats.wind_speed
    assert isinstance(legacy.explore(channel="load_[kN]", statistic="mean", show=False), go.Figure)


def test_calculation_contract(stats, monkeypatch):
    """Validate before calculation and copy metadata while preserving file order.

    Parameters
    ----------
    stats : All_stats
        Result returned by the calculation stub.
    monkeypatch : pytest.MonkeyPatch
        Fixture intercepting the underlying calculation.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_statistics_exploration.py -k calculation_contract
    """
    module = importlib.import_module("load_arena.process.concatenate_stats")
    calls = []
    monkeypatch.setattr(module, "concatenate_stats", lambda files, channels: (calls.append((files, channels)), stats)[1])
    files = [Path("b.int"), "a.int", "a.int", "c.int"]
    labels, speeds = list(stats.dlc), list(stats.wind_speed)
    result = calculate_statistics(files, dlc=labels, wind_speed=speeds, channels=["load_[kN]"])
    assert result is stats
    assert calls == [(files, ["load_[kN]"])]
    labels[0], speeds[0] = "changed", 999
    assert result.dlc[0] == "DLC12" and result.wind_speed[0] == 12
    with pytest.raises(ValueError, match="dlc"):
        calculate_statistics(files, dlc=[], wind_speed=speeds)
    with pytest.raises(ValueError, match="at least one"):
        calculate_statistics([], dlc=[], wind_speed=[])
    assert len(calls) == 1


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
