"""Contracts for exploration of stored family-average results."""

import copy

import pandas as pd
import plotly.graph_objects as go
import pytest

from load_arena.process.family_avg import FamilyAvg
from load_arena.visualization.family_avg_plots import plot_family_avg


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
        x_channel="WindSpeed_[m/s]", x_statistic=statistic,
        channel="TowerMx_[kNm]", statistic=statistic, plf=True, show=False,
    )
    trace = figure.data[0]
    assert list(trace.x) == [14.0 + offset, 18.0 + offset, 22.0 + offset]
    assert list(trace.y) == [110.0 + offset, 120.0 + offset, 130.0 + offset]
    assert figure.layout.xaxis.title.text == (
        f"{statistic}: WindSpeed_[m/s] (PLF-adjusted)"
    )
    assert "PLF-adjusted" in figure.layout.title.text
    assert "PLF adjusted: %{customdata[4]}" in trace.hovertemplate
    assert all(row[4] == "yes" for row in trace.customdata)


@pytest.mark.parametrize(
    "x_statistic,offset", [("mean", 0), ("std", 1), ("min", 2), ("max", 3)]
)
def test_independent_x_statistic_selection(family_stats, x_statistic, offset):
    """Select the x statistic independently from the y statistic.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    x_statistic : str
        Statistic selected for the numeric x-axis.
    offset : int
        Expected fixture offset for the selected x statistic.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k independent_x
    """
    series = family_stats.series(
        channel="TowerMx_[kNm]",
        statistic="max",
        x_channel="WindSpeed_[m/s]",
        x_statistic=x_statistic,
        plf=False,
    )

    assert list(series.x) == [4.0 + offset, 8.0 + offset, 12.0 + offset]
    assert list(series.y) == [13.0, 23.0, 33.0]
    assert series.x_label == f"{x_statistic}: WindSpeed_[m/s] (raw)"
    assert all(row[11] == x_statistic for row in series.metadata)
    assert all(row[12] == "no" for row in series.metadata)


@pytest.mark.parametrize(
    "plf,x_plf,expected_x,expected_mode",
    [
        (True, None, [14.0, 18.0, 22.0], "yes"),
        (True, False, [4.0, 8.0, 12.0], "no"),
        (False, True, [14.0, 18.0, 22.0], "yes"),
    ],
)
def test_independent_x_plf_selection(
    family_stats, plf, x_plf, expected_x, expected_mode,
):
    """Resolve default and explicit x PLF modes independently from y.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    plf : bool
        PLF mode selected for the y-axis.
    x_plf : bool or None
        Optional independent PLF mode selected for the x-axis.
    expected_x : list[float]
        Expected values from the resolved x table.
    expected_mode : str
        Expected Plotly metadata value for the resolved x PLF mode.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k independent_x_plf
    """
    figure = family_stats.explore(
        channel="TowerMx_[kNm]",
        statistic="max",
        x_channel="WindSpeed_[m/s]",
        x_statistic="mean",
        plf=plf,
        x_plf=x_plf,
        show=False,
    )

    trace = figure.data[0]
    assert list(trace.x) == expected_x
    expected_y = [113.0, 123.0, 133.0] if plf else [13.0, 23.0, 33.0]
    assert list(trace.y) == expected_y
    assert all(row[12] == expected_mode for row in trace.customdata)
    assert "X value: %{x}" in trace.hovertemplate
    assert "X statistic: %{customdata[11]}" in trace.hovertemplate
    assert "X PLF adjusted: %{customdata[12]}" in trace.hovertemplate


def test_family_axis_ignores_x_only_options(family_stats):
    """Ignore x statistic and PLF options when family labels form the x-axis.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k ignores_x_only
    """
    figure = family_stats.explore(
        channel="TowerMx_[kNm]",
        statistic="mean",
        x_channel=None,
        x_statistic="unsupported",
        x_plf="unsupported",
        show=False,
    )

    trace = figure.data[0]
    assert list(trace.x) == ["DLC12", "DLC13", "DLC14"]
    assert all(list(row[10:]) == ["Family", None, None] for row in trace.customdata)
    assert "X statistic:" not in trace.hovertemplate


def test_removed_x_keyword_is_rejected(family_stats):
    """Reject the removed x keyword across family plotting entry points.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k removed_x
    """
    with pytest.raises(TypeError):
        family_stats.series(
            channel="TowerMx_[kNm]", statistic="mean", x="WindSpeed_[m/s]",
        )
    with pytest.raises(TypeError):
        family_stats.explore(
            channel="TowerMx_[kNm]", statistic="mean", x="WindSpeed_[m/s]",
        )
    with pytest.raises(TypeError):
        plot_family_avg(
            family_stats,
            channel="TowerMx_[kNm]",
            statistic="mean",
            x="WindSpeed_[m/s]",
        )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"x_statistic": "median"}, "statistic"),
        ({"x_plf": 1}, "plf"),
    ],
)
def test_invalid_numeric_x_table_options(family_stats, kwargs, match):
    """Reject invalid x table options when a numeric x-channel uses them.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    kwargs : dict
        Invalid independent x-axis selection.
    match : str
        Expected validation message fragment.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k numeric_x_table_options
    """
    arguments = {
        "channel": "TowerMx_[kNm]",
        "statistic": "mean",
        "x_channel": "WindSpeed_[m/s]",
        "show": False,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=match):
        family_stats.explore(**arguments)


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
        channel="TowerMx_[kNm]", statistic="max",
        x_channel="WindSpeed_[m/s]", x_statistic="mean", x_plf=True,
        show=False,
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


@pytest.mark.parametrize("kind,trace_type,mode", [
    ("scatter", "scatter", "markers"),
    ("bar", "bar", None),
    ("line", "scatter", "lines+markers"),
])
def test_explore_supports_common_plot_kinds(family_stats, kind, trace_type, mode):
    """Expose every common plot kind while retaining family point metadata.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    kind : str
        Requested common plot kind.
    trace_type : str
        Expected Plotly trace type.
    mode : str or None
        Expected scatter mode, or None for bar traces.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k common_plot_kinds
    """
    figure = family_stats.explore(
        channel="TowerMx_[kNm]", statistic="mean", kind=kind, show=False,
    )

    trace = figure.data[0]
    assert trace.type == trace_type
    if mode is not None:
        assert trace.mode == mode
    assert list(trace.x) == ["DLC12", "DLC13", "DLC14"]
    assert [row[0] for row in trace.customdata] == ["DLC12", "DLC13", "DLC14"]


def test_line_kind_sorts_numeric_x_with_aligned_family_metadata(family_stats):
    """Sort numeric family x-values while keeping y and provenance aligned.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k sorts_numeric_x
    """
    family_stats.mean["WindSpeed_[m/s]"] = [12.0, 4.0, 8.0]

    figure = family_stats.explore(
        x_channel="WindSpeed_[m/s]", channel="TowerMx_[kNm]",
        statistic="mean", kind="line", show=False,
    )

    trace = figure.data[0]
    assert list(trace.x) == [4.0, 8.0, 12.0]
    assert list(trace.y) == [20.0, 30.0, 10.0]
    assert [row[0] for row in trace.customdata] == ["DLC13", "DLC14", "DLC12"]


@pytest.mark.parametrize("kind", ["scatter", "bar", "line"])
def test_plot_family_avg_wrapper_forwards_kind(family_stats, kind):
    """Forward each supported plot kind through the compatibility wrapper.

    Parameters
    ----------
    family_stats : FamilyAvg
        Synthetic family result fixture.
    kind : str
        Plot kind passed through the legacy wrapper.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_family_avg_exploration.py -k wrapper_forwards
    """
    figure = plot_family_avg(
        family_stats,
        channel="TowerMx_[kNm]",
        statistic="mean",
        x_channel="WindSpeed_[m/s]",
        x_statistic="std",
        plf=True,
        x_plf=False,
        kind=kind,
    )

    assert figure.data[0].type == ("bar" if kind == "bar" else "scatter")
    assert list(figure.data[0].x) == [5.0, 9.0, 13.0]
    assert list(figure.data[0].y) == [110.0, 120.0, 130.0]
    if kind != "bar":
        assert figure.data[0].mode == (
            "lines+markers" if kind == "line" else "markers"
        )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"statistic": "median"}, "statistic"),
        ({"plf": 1}, "plf"),
        ({"channel": "missing"}, "exactly one"),
        ({"x_channel": "missing"}, "exactly one"),
        ({"x_channel": 42}, "x_channel"),
        ({"kind": "pie"}, "kind"),
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
            x_channel="WindSpeed_[m/s]", channel="TowerMx_[kNm]",
            statistic="mean", show=False,
        )
