"""Campaign FLS tests against independently computed reference damage."""

from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from load_arena.process.calc_del import calc_del
from load_arena.process.fls import calc_fls


@pytest.fixture
def fls_inputs(monkeypatch):
    """Supply three unequal cases and four numeric channels without file I/O.

    Parameters: monkeypatch replaces only the reader and DataFrame conversion.
    Returns: Case table and corresponding sample DataFrames.
    Examples: Use fls_inputs in a campaign aggregation test.
    """
    samples = [pd.DataFrame({"time": [0., 1., 2., 3., 4.],
                            "load": np.array([0., 2., 0., -2., 0.]) * scale,
                            "other": np.array([0., 4., 0., -4., 0.]) * scale,
                            "azimuth": [0., 90., 180., 270., 360.],
                            "label": ["x"] * 5}) for scale in (1, 2, 3)]
    readers = []
    for sample in samples:
        reader = Mock()
        reader.ReadAll.return_value = sample
        reader.ChInfo = None
        readers.append(reader)
    monkeypatch.setattr("load_arena.process.fls.ReadHawc2", Mock(side_effect=readers))
    monkeypatch.setattr("load_arena.process.fls.toDataFrame", lambda data, info: data)
    cases = pd.DataFrame({"Folder": ["."] * 3, "Case_folder": ["dlc"] * 3,
                          "Timeseries": ["a", "b", "c"], "Occurrences": [2., 5., 0.]})
    return cases, samples


@pytest.mark.parametrize("method", ["astm", "windap"])
def test_multi_channel_multi_exponent_weighting(fls_inputs, method):
    """Keep channels and exponents separate and weight complete-record damage.

    Parameters: fls_inputs supplies samples; method chooses the rainflow algorithm.
    Returns: None; output equals independently weighted per-signal DELs.
    Examples: pytest tests/test_fls.py -k weighting
    """
    cases, samples = fls_inputs
    result = calc_fls(cases, [4, 6, 8, 10, 12], 100, method)
    assert len(result.per_case) == 3 * 4 * 5
    assert len(result.campaign) == 4 * 5
    assert set(result.per_case.channel) == {"time", "load", "other", "azimuth"}
    assert set(result.per_case.case_row) == {2, 3, 4}
    assert result.n_ref == 100
    assert result.method == method
    for row in result.campaign.itertuples():
        exponent = row.wohler_exponent
        values = [calc_del(sample[row.channel], exponent, 100, method=method) for sample in samples]
        expected = (2 * values[0] ** exponent + 5 * values[1] ** exponent) ** (1 / exponent)
        assert row.DEL == pytest.approx(expected)
    if method == "astm":
        # Turning points 0, 2, -2, 0 leave half cycles of ranges 2, 4, 2.
        for exponent in (4, 6, 8, 10, 12):
            row = result.per_case.query("case_row == 2 and channel == 'load' and wohler_exponent == @exponent")
            assert row.DEL.iloc[0] == pytest.approx(((2**exponent + 0.5 * 4**exponent) / 100) ** (1 / exponent))


def test_duplicate_exponents_do_not_double_weight(fls_inputs):
    """Calculate each requested exponent once even when the list repeats it.

    Parameters: fls_inputs supplies sample records and occurrences.
    Returns: None; duplicate exponents leave damage weighting unchanged.
    Examples: pytest tests/test_fls.py -k duplicate
    """
    cases, samples = fls_inputs
    result = calc_fls(cases, [4, 4], 100, "astm")
    assert len(result.campaign) == 4
    expected = (2 * calc_del(samples[0]["load"], 4, 100, "astm")**4 +
                5 * calc_del(samples[1]["load"], 4, 100, "astm")**4)**0.25
    assert result.campaign.query("channel == 'load'").DEL.iloc[0] == pytest.approx(expected)


def test_zero_occurrences(fls_inputs):
    """Return zero campaign DEL when every occurrence count is zero.

    Parameters: fls_inputs supplies cases and varying numeric signals.
    Returns: None; per-case DELs remain available while campaign DELs are zero.
    Examples: pytest tests/test_fls.py -k zero_occurrences
    """
    cases, _ = fls_inputs
    cases["Occurrences"] = 0
    result = calc_fls(cases, [4, 10], 100, "astm")
    assert (result.campaign.DEL == 0).all()
    assert (result.per_case.DEL > 0).any()


def test_constant_channels_preserve_warning(fls_inputs):
    """Preserve existing zero-cycle results for constant numeric signals.

    Parameters: fls_inputs supplies mutable sample DataFrames.
    Returns: None; constant load channels warn and have zero DEL.
    Examples: pytest tests/test_fls.py -k constant
    """
    cases, samples = fls_inputs
    for sample in samples:
        sample["load"] = 1.0
    with pytest.warns(RuntimeWarning, match="no variation"):
        result = calc_fls(cases, [4, 10], 100, "astm")
    assert (result.campaign.query("channel == 'load'").DEL == 0).all()


def test_invalid_signal_has_case_channel_exponent_context(fls_inputs):
    """Reject invalid numeric signals with actionable source context.

    Parameters: fls_inputs supplies a signal that can be corrupted.
    Returns: None; failure identifies row, channel, and Wöhler exponent.
    Examples: pytest tests/test_fls.py -k invalid_signal
    """
    cases, samples = fls_inputs
    samples[0].loc[1, "load"] = np.nan
    with pytest.raises(ValueError, match="CSV row 2.*channel load.*wohler_exponent 4"):
        calc_fls(cases, [4], 100, "astm")


@pytest.mark.parametrize("exponents,n_ref,method", [([], 100, "astm"), ([0], 100, "astm"),
    ([True], 100, "astm"), ([float("inf")], 100, "astm"), ([4], 0, "astm"),
    ([4], True, "astm"), ([4], 100, "bad")])
def test_invalid_fls_parameters(fls_inputs, exponents, n_ref, method):
    """Validate direct campaign-function parameters before reading samples.

    Parameters: fls_inputs supplies cases; remaining arguments are invalid options.
    Returns: None; invalid calls raise ValueError.
    Examples: pytest tests/test_fls.py -k invalid_fls_parameters
    """
    cases, _ = fls_inputs
    with pytest.raises(ValueError):
        calc_fls(cases, exponents, n_ref, method)
