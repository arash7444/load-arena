"""Contracts for result-independent and combined plotting."""

import copy
import importlib

import pandas as pd
import pytest

from load_arena import PlotSeries, plot
from load_arena.process.concatenate_stats import All_stats
from load_arena.process.family_avg import FamilyAvg


def _all_stats() -> All_stats:
    """Create stored simulation statistics for common plotting tests.

    Parameters
    ----------
    None

    Returns
    -------
    All_stats
        Two-simulation result with wind-speed and power channels.

    Examples
    --------
    >>> len(_all_stats().filename)
    2
    """
    tables = {
        statistic: pd.DataFrame(
            {
                "Aerot._[kW]": [100.0 + offset, 200.0 + offset],
                "WSPgl._[m/s]": [8.0, 12.0],
            },
            index=[9, 2],
        )
        for offset, statistic in enumerate(("mean", "std", "min", "max"))
    }
    return All_stats(
        **tables,
        **{f"{name}_plf": table * 1.5 for name, table in tables.items()},
        filename=[r"D:\results\case_01.int", r"D:\results\case_02.int"],
        family=["DLC12", "DLC12"],
    )


def _family_stats() -> FamilyAvg:
    """Create stored family averages with complete point provenance.

    Parameters
    ----------
    None

    Returns
    -------
    FamilyAvg
        Two-family result aligned with member and contributor paths.

    Examples
    --------
    >>> _family_stats().family_name
    ['DLC12', 'DLC13']
    """
    tables = {
        statistic: pd.DataFrame(
            {
                "Family": ["DLC12", "DLC13"],
                "Aerot._[kW]": [150.0 + offset, 250.0 + offset],
                "WSPgl._[m/s]": [8.0, 12.0],
            },
            index=[7, 3],
        )
        for offset, statistic in enumerate(("mean", "std", "min", "max"))
    }
    filenames = [
        (r"D:\results\case_01.int", r"D:\results\case_02.int"),
        (r"D:\results\case_03.int",),
    ]
    provenance = pd.DataFrame(
        [
            {
                "Family": family,
                "statistic": "mean",
                "plf_adjusted": False,
                "channel": "Aerot._[kW]",
                "channel_position": 0,
                "value": 150.0 + 100.0 * row,
                "averaging_method": "mean",
                "member_count": len(filenames[row]),
                "member_files": filenames[row],
                "contributing_files": filenames[row],
                "source_file": None,
            }
            for row, family in enumerate(("DLC12", "DLC13"))
        ]
    )
    return FamilyAvg(
        **tables,
        **{f"{name}_plf": table.copy() for name, table in tables.items()},
        filename=[list(paths) for paths in filenames],
        family_name=["DLC12", "DLC13"],
        case_folder=["DLC12", "DLC13"],
        provenance=provenance,
    )


def test_combines_statistics_and_family_average_without_recalculation(monkeypatch):
    """Combine stored result types while preserving values and provenance.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture replacing calculation functions with failure sentinels.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_common_plotting.py -k combines
    """
    statistics = _all_stats()
    family_stats = _family_stats()
    statistics_before = copy.deepcopy(statistics)
    family_before = copy.deepcopy(family_stats)
    statistics_module = importlib.import_module("load_arena.process.concatenate_stats")
    family_module = importlib.import_module("load_arena.process.family_avg")
    monkeypatch.setattr(
        statistics_module,
        "concatenate_stats",
        lambda *args, **kwargs: pytest.fail("statistics recalculated"),
    )
    monkeypatch.setattr(
        family_module,
        "calc_family_avg",
        lambda *args, **kwargs: pytest.fail("family averages recalculated"),
    )

    simulation_series = statistics.series(
        channel="Aerot._[kW]",
        statistic="max",
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        name="Simulations",
    )
    family_series = family_stats.series(
        channel="Aerot._[kW]",
        statistic="mean",
        x="WSPgl._[m/s]",
        plf=False,
        name="Family average",
    )
    figure = plot(simulation_series, family_series, kind="scatter")

    assert len(figure.data) == 2
    assert [trace.name for trace in figure.data] == ["Simulations", "Family average"]
    assert list(figure.data[0].x) == [8.0, 12.0]
    assert list(figure.data[0].y) == [103.0, 203.0]
    assert list(figure.data[1].x) == [8.0, 12.0]
    assert list(figure.data[1].y) == [150.0, 250.0]
    assert figure.data[0].customdata[0][0] == "case_01.int"
    assert figure.data[0].customdata[0][2] == r"D:\results\case_01.int"
    assert list(figure.data[1].customdata[0][5]) == [
        r"D:\results\case_01.int", r"D:\results\case_02.int",
    ]
    assert "Channel: %{customdata[3]}" in figure.data[0].hovertemplate
    assert "Channel: %{customdata[2]}" in figure.data[1].hovertemplate
    assert figure.layout.xaxis.title.text == "mean: WSPgl._[m/s]"
    assert figure.layout.yaxis.title.text == "Y"
    assert figure.layout.title.text == "Y"
    for name, value in vars(statistics_before).items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(getattr(statistics, name), value)
        else:
            assert getattr(statistics, name) == value
    for name, value in vars(family_before).items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(getattr(family_stats, name), value)
        else:
            assert getattr(family_stats, name) == value


def test_line_sorts_numeric_x_and_preserves_categorical_x_order():
    """Apply line ordering according to each series' declared x kind.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_common_plotting.py -k line_sorts
    """
    numeric = PlotSeries(
        x=[12, 4, 8], y=[3, 1, 2], name="Numeric",
        x_label="Speed", y_label="Load", title="Load",
        metadata=[[12], [4], [8]], hovertemplate="%{y}", x_kind="numeric",
    )
    categorical = PlotSeries(
        x=["DLC13", "DLC12", "DLC14"], y=[3, 1, 2], name="Categorical",
        x_label="Family", y_label="Load", title="Load",
        metadata=[["DLC13"], ["DLC12"], ["DLC14"]],
        hovertemplate="%{y}", x_kind="categorical",
    )

    figure = plot(numeric, categorical, kind="line")

    assert list(figure.data[0].x) == [4, 8, 12]
    assert list(figure.data[0].y) == [1, 2, 3]
    assert list(figure.data[1].x) == ["DLC13", "DLC12", "DLC14"]
    assert list(figure.data[1].y) == [3, 1, 2]


@pytest.mark.parametrize("kind", ["scatter", "bar"])
@pytest.mark.parametrize(
    "x_values,x_kind",
    [([12.0, 4.0], "numeric"), (["DLC13", "DLC12"], "categorical")],
)
def test_scatter_and_bar_accept_numeric_or_categorical_x(kind, x_values, x_kind):
    """Keep numeric and categorical x-values unchanged for scatter and bar.

    Parameters
    ----------
    kind : str
        Plot kind under test.
    x_values : list
        Numeric or categorical x-values to preserve.
    x_kind : str
        Declared interpretation of the x-values.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_common_plotting.py -k scatter_and_bar
    """
    series = PlotSeries(
        x=x_values, y=[1.0, 2.0], name="Values",
        x_label="X", y_label="Y", title="Y",
        metadata=[[0], [1]], hovertemplate="%{y}", x_kind=x_kind,
    )

    figure = plot(series, kind=kind)

    assert list(figure.data[0].x) == x_values
    assert list(figure.data[0].y) == [1.0, 2.0]


@pytest.mark.parametrize(
    "series,match",
    [
        ([], "at least one"),
        (["not a series"], "only PlotSeries"),
    ],
)
def test_plot_rejects_only_structurally_invalid_inputs(series, match):
    """Reject missing or incorrectly typed traces without comparing semantics.

    Parameters
    ----------
    series : list
        Invalid positional arguments supplied to plot.
    match : str
        Expected validation message fragment.

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_common_plotting.py -k structurally_invalid
    """
    with pytest.raises(ValueError, match=match):
        plot(*series)


def test_plot_series_rejects_misaligned_rows():
    """Reject a series whose point metadata is not row-aligned.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> # Run: pytest tests/test_common_plotting.py -k misaligned_rows
    """
    with pytest.raises(ValueError, match="same number"):
        PlotSeries(
            x=[1, 2], y=[3, 4], name="Broken", x_label="X", y_label="Y",
            title="Y", metadata=[[1]], hovertemplate="%{y}", x_kind="numeric",
        )
