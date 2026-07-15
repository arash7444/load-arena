import numpy as np
import pandas as pd
import pytest

from load_arena.process import RainflowResult, calc_del, calculate_rainflow


def test_calculate_rainflow_returns_astm_cycles_and_metadata():
    """Verify ASTM counting returns the expected cycles and metadata.

    Parameters
    ----------
    None
        This test creates its signal internally.

    Returns
    -------
    None
        The test passes when ASTM cycle data and metadata are correct.

    Examples
    --------
    >>> test_calculate_rainflow_returns_astm_cycles_and_metadata()
    """
    result = calculate_rainflow(np.array([0.0, 2.0, 0.0]), method="astm")

    assert isinstance(result, RainflowResult)
    assert result.method == "astm"
    assert result.levels is None
    assert result.threshold is None
    pd.testing.assert_frame_equal(
        result.cycles,
        pd.DataFrame(
            {
                "range": [2.0, 2.0],
                "mean": [1.0, 1.0],
                "count": [0.5, 0.5],
            }
        ),
    )


def test_calculate_rainflow_returns_windap_cycles_and_metadata():
    """Verify Windap counting returns the expected cycles and parameters.

    Parameters
    ----------
    None
        This test creates its signal internally.

    Returns
    -------
    None
        The test passes when Windap cycle data and metadata are correct.

    Examples
    --------
    >>> test_calculate_rainflow_returns_windap_cycles_and_metadata()
    """
    result = calculate_rainflow(np.array([0.0, 2.0, 0.0]), method="windap")

    assert result.method == "windap"
    assert result.levels == 255
    assert result.threshold == pytest.approx(255 / 50)
    assert result.range.tolist() == pytest.approx([2.0, 2.0])
    assert result.mean.tolist() == pytest.approx([1.0, 1.0])
    assert result.count.tolist() == [0.5, 0.5]


def test_rainflow_results_are_independent():
    """Verify later calculations cannot overwrite an earlier result.

    Parameters
    ----------
    None
        This test creates both signals internally.

    Returns
    -------
    None
        The test passes when results are distinct and retain their own data.

    Examples
    --------
    >>> test_rainflow_results_are_independent()
    """
    first = calculate_rainflow(np.array([0.0, 1.0, 0.0]), method="astm")
    second = calculate_rainflow(np.array([0.0, 2.0, 0.0]), method="astm")

    assert first is not second
    assert first.range.tolist() == [1.0, 1.0]
    assert second.range.tolist() == [2.0, 2.0]


@pytest.mark.parametrize("method", ["windap", "astm"])
@pytest.mark.parametrize(
    "signal",
    [
        pd.Series([3.0, 3.0, 3.0], dtype="Float64"),
        pd.Series([3.0], dtype="Float64"),
    ],
)
def test_constant_signal_warns_and_returns_zero_damage(method, signal):
    """Verify constant signals produce zero cycles and zero DEL.

    Parameters
    ----------
    method : str
        Rainflow method supplied by pytest.
    signal : pandas.Series
        Constant or single-value signal supplied by pytest.

    Returns
    -------
    None
        The test passes when the signal warns and produces zero fatigue damage.

    Examples
    --------
    >>> signal = pd.Series([3.0], dtype="Float64")
    >>> test_constant_signal_warns_and_returns_zero_damage("astm", signal)
    """
    with pytest.warns(RuntimeWarning, match="no variation"):
        result = calculate_rainflow(signal, method=method)
    with pytest.warns(RuntimeWarning, match="no variation"):
        del_value = calc_del(signal, 4, 100, method=method)

    assert result.cycles.empty
    assert result.cycles.dtypes.tolist() == [float, float, float]
    assert del_value == 0.0


@pytest.mark.parametrize(
    "signal",
    [
        np.array([]),
        np.array([0.0, np.nan, 1.0]),
        np.array([0.0, np.inf, 1.0]),
        np.array([[0.0, 1.0]]),
        pd.Series([0.0, pd.NA, 1.0], dtype="Float64"),
    ],
)
def test_calculate_rainflow_rejects_invalid_signal(signal):
    """Verify empty, missing, infinite, and multidimensional signals fail.

    Parameters
    ----------
    signal : numpy.ndarray or pandas.Series
        Invalid signal supplied by pytest.

    Returns
    -------
    None
        The test passes when validation raises ``ValueError``.

    Examples
    --------
    >>> test_calculate_rainflow_rejects_invalid_signal(np.array([]))
    """
    with pytest.raises(ValueError):
        calculate_rainflow(signal)


def test_calculate_rainflow_rejects_nonnumeric_signal():
    """Verify nonnumeric pandas values produce a clear type error.

    Parameters
    ----------
    None
        This test creates its signal internally.

    Returns
    -------
    None
        The test passes when conversion raises ``TypeError``.

    Examples
    --------
    >>> test_calculate_rainflow_rejects_nonnumeric_signal()
    """
    with pytest.raises(TypeError, match="numeric"):
        calculate_rainflow(pd.Series(["low", "high"]))


@pytest.mark.parametrize(
    ("kwargs", "exception_type"),
    [
        ({"method": "unknown"}, ValueError),
        ({"levels": 0}, ValueError),
        ({"levels": 12.5}, TypeError),
        ({"threshold": 0}, ValueError),
        ({"threshold": np.inf}, ValueError),
    ],
)
def test_calculate_rainflow_validates_method_parameters(kwargs, exception_type):
    """Verify invalid method and Windap parameters are rejected.

    Parameters
    ----------
    kwargs : dict
        Invalid keyword arguments supplied by pytest.
    exception_type : type[Exception]
        Expected validation exception.

    Returns
    -------
    None
        The test passes when the expected exception is raised.

    Examples
    --------
    >>> test_calculate_rainflow_validates_method_parameters(
    ...     {"method": "unknown"}, ValueError
    ... )
    """
    with pytest.raises(exception_type):
        calculate_rainflow(np.array([0.0, 1.0, 0.0]), **kwargs)


def test_windap_threshold_can_filter_all_cycles():
    """Verify Windap returns an empty table when its threshold removes all cycles.

    Parameters
    ----------
    None
        This test creates its signal internally.

    Returns
    -------
    None
        The test passes when no zero-range placeholder cycle is returned.

    Examples
    --------
    >>> test_windap_threshold_can_filter_all_cycles()
    """
    result = calculate_rainflow(
        np.array([0.0, 2.0, 0.0]),
        method="windap",
        threshold=300,
    )

    assert result.cycles.empty


def test_calc_del_supports_both_counting_methods():
    """Verify DEL calculation forwards ASTM and Windap method selection.

    Parameters
    ----------
    None
        This test creates its signal internally.

    Returns
    -------
    None
        The test passes when both methods produce the known DEL.

    Examples
    --------
    >>> test_calc_del_supports_both_counting_methods()
    """
    signal = np.array([0.0, 2.0, 0.0])

    assert calc_del(signal, 4, 1, method="astm") == pytest.approx(2.0)
    assert calc_del(signal, 4, 1, method="windap") == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("wohler_exponent", "n_ref", "exception_type"),
    [
        (0, 1, ValueError),
        (np.inf, 1, ValueError),
        ("4", 1, TypeError),
        (4, 0, ValueError),
        (4, np.nan, ValueError),
        (4, "1", TypeError),
    ],
)
def test_calc_del_validates_damage_parameters(
    wohler_exponent,
    n_ref,
    exception_type,
):
    """Verify invalid Wohler and reference-cycle parameters are rejected.

    Parameters
    ----------
    wohler_exponent : object
        Candidate exponent supplied by pytest.
    n_ref : object
        Candidate reference cycle count supplied by pytest.
    exception_type : type[Exception]
        Expected validation exception.

    Returns
    -------
    None
        The test passes when invalid damage parameters raise as expected.

    Examples
    --------
    >>> test_calc_del_validates_damage_parameters(0, 1, ValueError)
    """
    with pytest.raises(exception_type):
        calc_del(np.array([0.0, 1.0, 0.0]), wohler_exponent, n_ref)
