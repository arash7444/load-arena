"""Contracts for exploration of stored family-average results."""

import copy

import pandas as pd
import plotly.graph_objects as go
import pytest

from load_arena.process.family_avg import FamilyAvg


@pytest.fixture
def family_stats():
    """Create a synthetic family result with distinct raw and PLF values.

    Parameters
    ----------
    None

    Returns
    -------
    FamilyAvg
        Three-family result with row-aligned metadata and statistic tables.

    Examples
    --------
    >>> result = family_stats.__wrapped__()
    """
    raw_tables = {}
    plf_tables = {}
    for offset, statistic in enumerate(("mean", "std", "min", "max")):
        raw_tables[statistic] = pd.DataFrame(
            {
                "Family": ["DLC12", "DLC13", "DLC14"],
                "TowerMx_[kNm]": [10.0 + offset, 20.0 + offset, 30.0 + offset],
                "WindSpeed_[m/s]": [4.0 + offset, 8.0 + offset, 12.0 + offset],
            },
            index=[8, 2, 6],
        )
        plf_tables[f"{statistic}_plf"] = pd.DataFrame(
            {
                "Family": ["DLC12", "DLC13", "DLC14"],
                "TowerMx_[kNm]": [110.0 + offset, 120.0 + offset, 130.0 + offset],
                "WindSpeed_[m/s]": [14.0 + offset, 18.0 + offset, 22.0 + offset],
            },
            index=[4, 9, 1],
        )
    return FamilyAvg(
        **raw_tables,
        **plf_tables,
        filename=[
            [r"D:\results\DLC12\case_001.int", r"D:\results\DLC12\case_002.int"],
            [r"D:\results\DLC13\case_003.int"],
            [r"D:\results\DLC14\case_004.int"],
        ],
        family_name=["DLC12", "DLC13", "DLC14"],
        case_folder=["DLC12", "DLC13", "DLC14"],
    )


@pytest.mark.parametrize(
    "statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)]
)
def test_raw_table_selection_and_family_alignment(family_stats, statistic, offset):
    """Use the requested raw table and preserve stored family row order.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    statistic : str
        Requested raw statistic.
    offset : int
        Expected statistic-specific value offset.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k raw_table
    """
    figure = family_stats.explore(
        channel="TowerMx_[kNm]", statistic=statistic, show=False,
    )
    trace = figure.data[0]
    assert list(trace.x) == ["DLC12", "DLC13", "DLC14"]
    assert list(trace.y) == [10.0 + offset, 20.0 + offset, 30.0 + offset]
    assert trace.mode == "markers"
    assert figure.layout.xaxis.title.text == "Family"
    assert figure.layout.yaxis.title.text == f"{statistic}: TowerMx_[kNm]"
    assert "raw" in figure.layout.title.text


@pytest.mark.parametrize(
    "statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)]
)
def test_plf_table_and_channel_x_selection(family_stats, statistic, offset):
    """Use one PLF table for both numeric axes without index alignment.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    statistic : str
        Requested PLF statistic.
    offset : int
        Expected statistic-specific value offset.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k plf_table
    """
    figure = family_stats.explore(
        x="WindSpeed_[m/s]", channel="TowerMx_[kNm]",
        statistic=statistic, plf=True, show=False,
    )
    trace = figure.data[0]
    assert list(trace.x) == [14.0 + offset, 18.0 + offset, 22.0 + offset]
    assert list(trace.y) == [110.0 + offset, 120.0 + offset, 130.0 + offset]
    assert figure.layout.xaxis.title.text == f"{statistic}: WindSpeed_[m/s]"
    assert "PLF-adjusted" in figure.layout.title.text
    assert "PLF adjusted: %{customdata[4]}" in trace.hovertemplate
    assert all(row[4] == "yes" for row in trace.customdata)


def test_hover_uses_basenames_and_retains_full_paths(family_stats):
    """Expose readable basenames while retaining source paths in plot metadata.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k basenames
    """
    provenance_rows = []
    for family, files in zip(family_stats.family_name, family_stats.filename):
        provenance_rows.append(
            {
                "Family": family,
                "statistic": "max",
                "plf_adjusted": False,
                "channel": "TowerMx_[kNm]",
                "channel_position": 0,
                "value": 0.0,
                "averaging_method": "mean_half",
                "member_count": len(files),
                "member_files": tuple(files),
                "contributing_files": tuple(files[:1]),
                "source_file": None,
            }
        )
    family_stats.provenance = pd.DataFrame(provenance_rows)
    provenance_before = family_stats.provenance.copy(deep=True)

    figure = family_stats.explore(
        channel="TowerMx_[kNm]", statistic="max", show=False,
    )
    first = figure.data[0].customdata[0]
    assert first[0] == "DLC12"
    assert first[1] == "case_001.int, case_002.int"
    assert list(first[5]) == [
        r"D:\results\DLC12\case_001.int", r"D:\results\DLC12\case_002.int"
    ]
    assert first[6] == "mean_half"
    assert first[7] == 2
    assert list(first[8]) == [r"D:\results\DLC12\case_001.int"]
    assert "Averaging method: %{customdata[6]}" in figure.data[0].hovertemplate
    assert "Member count: %{customdata[7]}" in figure.data[0].hovertemplate
    assert r"D:\results" not in figure.data[0].hovertemplate
    pd.testing.assert_frame_equal(family_stats.provenance, provenance_before)


def test_show_control_and_result_immutability(family_stats, monkeypatch):
    """Control display and leave every stored result field unchanged.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    monkeypatch : pytest.MonkeyPatch
        Fixture intercepting Plotly display.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k show_control
    """
    before = copy.deepcopy(family_stats)
    displayed = []
    monkeypatch.setattr(go.Figure, "show", lambda self: displayed.append(self))

    hidden = family_stats.explore(
        channel="TowerMx_[kNm]", statistic="mean", show=False,
    )
    shown = family_stats.explore(channel="TowerMx_[kNm]", statistic="mean")
    assert isinstance(hidden, go.Figure)
    assert displayed == [shown]
    for name, value in vars(before).items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(getattr(family_stats, name), value)
        else:
            assert getattr(family_stats, name) == value


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"statistic": "median"}, "statistic"),
        ({"plf": 1}, "plf"),
        ({"channel": "missing"}, "exactly one"),
        ({"x": "missing"}, "exactly one"),
        ({"x": None}, "x must"),
    ],
)
def test_invalid_arguments(family_stats, kwargs, match):
    """Reject unsupported statistics, PLF values, and axis selections.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    kwargs : dict
        Invalid keyword overrides.
    match : str
        Expected validation error text.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k invalid_arguments
    """
    arguments = {
        "channel": "TowerMx_[kNm]", "statistic": "mean", "show": False,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=match):
        family_stats.explore(**arguments)


@pytest.mark.parametrize("failure", ["empty", "duplicate", "family_length", "family_order", "filename"])
def test_invalid_table_and_metadata(family_stats, failure):
    """Reject empty, ambiguous, or row-misaligned family results.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    failure : str
        Invalid table or metadata scenario.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k invalid_table
    """
    if failure == "empty":
        family_stats.mean = family_stats.mean.iloc[0:0]
    elif failure == "duplicate":
        family_stats.mean = pd.concat([family_stats.mean, family_stats.mean[["TowerMx_[kNm]"]]], axis=1)
    elif failure == "family_length":
        family_stats.family_name = ["DLC12"]
    elif failure == "family_order":
        family_stats.family_name = ["DLC13", "DLC12", "DLC14"]
    else:
        family_stats.filename = family_stats.filename[:-1]
    with pytest.raises(ValueError):
        family_stats.explore(
            channel="TowerMx_[kNm]", statistic="mean", show=False,
        )


@pytest.mark.parametrize("axis,value", [("y", float("nan")), ("y", "bad"), ("x", float("inf")), ("x", True)])
def test_invalid_numeric_values(family_stats, axis, value):
    """Reject nonnumeric and nonfinite values from either numeric axis.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    axis : str
        Axis whose selected value is invalid.
    value : object
        Invalid value inserted into the stored table.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k invalid_numeric
    """
    selected = "TowerMx_[kNm]" if axis == "y" else "WindSpeed_[m/s]"
    family_stats.mean[selected] = family_stats.mean[selected].astype(object)
    family_stats.mean.loc[family_stats.mean.index[1], selected] = value
    with pytest.raises(ValueError, match=f"{axis}-axis"):
        family_stats.explore(
            x="WindSpeed_[m/s]", channel="TowerMx_[kNm]",
            statistic="mean", show=False,
        )
