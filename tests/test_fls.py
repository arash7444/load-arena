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
        reader.t = sample["time"].to_numpy()
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
    result = calc_fls(cases, [4, 6, 8, 10, 12], 100, method, channels=["load", "other"])
    assert list(result.channels) == ["load", "other"]
    assert result.n_ref == 100
    assert result.method == method
    for name, channel in result.channels.items():
        assert len(channel.files) == 3
        assert channel.files.case_row.tolist() == [2, 3, 4]
        assert len(channel.campaign) == 5
        for row in channel.campaign.itertuples():
            exponent = row.wohler_exponent
            values = [calc_del(sample[name], exponent, 100, method=method) for sample in samples]
            expected = (2 * values[0] ** exponent + 5 * values[1] ** exponent) ** (1 / exponent)
            assert row.DEL == pytest.approx(expected)
            assert channel.files[f"DEL_m{int(exponent)}"].tolist() == pytest.approx(values)
    if method == "astm":
        for exponent in (4, 6, 8, 10, 12):
            assert result.channels["load"].files[f"DEL_m{exponent}"].iloc[0] == pytest.approx(
                ((2**exponent + 0.5 * 4**exponent) / 100) ** (1 / exponent))


def test_duplicate_exponents_do_not_double_weight(fls_inputs):
    """Calculate each requested exponent once even when the list repeats it.

    Parameters: fls_inputs supplies sample records and occurrences.
    Returns: None; duplicate exponents leave damage weighting unchanged.
    Examples: pytest tests/test_fls.py -k duplicate
    """
    cases, samples = fls_inputs
    result = calc_fls(cases, [4, 4], 100, "astm", channels=["load", "other"])
    assert all(len(ch.campaign) == 1 for ch in result.channels.values())
    expected = (2 * calc_del(samples[0]["load"], 4, 100, "astm")**4 +
                5 * calc_del(samples[1]["load"], 4, 100, "astm")**4)**0.25
    assert result.channels["load"].campaign.DEL.iloc[0] == pytest.approx(expected)


def test_zero_occurrences(fls_inputs):
    """Return zero campaign DEL when every occurrence count is zero.

    Parameters: fls_inputs supplies cases and varying numeric signals.
    Returns: None; per-case DELs remain available while campaign DELs are zero.
    Examples: pytest tests/test_fls.py -k zero_occurrences
    """
    cases, _ = fls_inputs
    cases["Occurrences"] = 0
    result = calc_fls(cases, [4, 10], 100, "astm", channels=["load", "other"])
    assert all((ch.campaign.DEL == 0).all() for ch in result.channels.values())
    assert (result.channels["load"].files.DEL_m4 > 0).any()


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
        result = calc_fls(cases, [4, 10], 100, "astm", channels=["load", "other"])
    assert (result.channels["load"].campaign.DEL == 0).all()
    assert (result.channels["load"].files.filter(like="DEL_1Hz").to_numpy() == 0).all()
    assert all(result.channels["load"].rainflow_results[row].cycles.empty for row in (2, 3, 4))


def test_invalid_signal_has_case_channel_context(fls_inputs):
    """Reject invalid numeric signals with actionable source context.

    Parameters: fls_inputs supplies a signal that can be corrupted.
    Returns: None; failure identifies row, channel, and Wöhler exponent.
    Examples: pytest tests/test_fls.py -k invalid_signal
    """
    cases, samples = fls_inputs
    samples[0].loc[1, "load"] = np.nan
    with pytest.raises(ValueError, match="CSV row 2.*channel load"):
        calc_fls(cases, [4], 100, "astm", channels=["load", "other"])


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
        calc_fls(cases, exponents, n_ref, method, channels=["load"])


@pytest.mark.parametrize("channels", [[], ["load", "load"], [""], [1], None])
def test_invalid_channels(fls_inputs, channels):
    """Reject invalid selections in direct FLS calls.

    Parameters: fls_inputs supplies cases; channels is an invalid selection.
    Returns: None; validation raises before simulation processing.
    Examples: pytest tests/test_fls.py -k invalid_channels
    """
    cases, _ = fls_inputs
    with pytest.raises(ValueError, match="channels"):
        calc_fls(cases, [4], 100, channels=channels)


def test_selected_channel_order(fls_inputs):
    """Preserve selection order, including explicitly selected time.

    Parameters: fls_inputs supplies simulation samples.
    Returns: None; result rows follow the explicit selection.
    Examples: pytest tests/test_fls.py -k selected_channel_order
    """
    cases, _ = fls_inputs
    result = calc_fls(cases, [4], 100, "astm", channels=["other", "time", "load"])
    assert list(result.channels) == ["other", "time", "load"]


@pytest.mark.parametrize("method", ["astm", "windap"])
def test_retained_rainflow_reused_for_both_references(fls_inputs, monkeypatch, method):
    """Retain one counting result per case/channel for every DEL reference.

    Parameters: fls_inputs supplies samples; monkeypatch spies on counting; method selects algorithm.
    Returns: None; cycle data, counts, durations, and reference DELs are verified.
    Examples: pytest tests/test_fls.py -k retained_rainflow
    """
    from load_arena.process.calculate_rainflow import calculate_rainflow
    cases, samples = fls_inputs
    cases["Timeseries"] = "repeated.int"
    readers = []
    for index, sample in enumerate(samples):
        reader = Mock()
        reader.ReadAll.return_value = sample
        reader.t = 100 + np.arange(len(sample)) * (index + 1)
        readers.append(reader)
    monkeypatch.setattr("load_arena.process.fls.ReadHawc2", Mock(side_effect=readers))
    counting = Mock(wraps=calculate_rainflow)
    monkeypatch.setattr("load_arena.process.fls.calculate_rainflow", counting)
    result = calc_fls(cases, [4, 6, 4], 100, method, channels=["load", "other"])
    assert counting.call_count == 6
    assert len({id(value) for ch in result.channels.values() for value in ch.rainflow_results.values()}) == 6
    for name, channel in result.channels.items():
        assert list(channel.rainflow_results) == [2, 3, 4]
        assert channel.files.columns.tolist() == [
            "case_row", "filename", "occurrences", "duration_s",
            "DEL_m4", "DEL_1Hz_m4", "DEL_m6", "DEL_1Hz_m6",
        ]
        assert channel.files.filename.nunique() == 1
        for case_row, retained in channel.rainflow_results.items():
            expected = calculate_rainflow(samples[case_row - 2][name], method=method)
            pd.testing.assert_frame_equal(retained.cycles, expected.cycles)
            assert (retained.method, retained.levels, retained.threshold) == (expected.method, expected.levels, expected.threshold)
        for row in channel.files.itertuples():
            assert row.duration_s == 4 * (row.case_row - 1)
            for exponent in (4, 6):
                value = getattr(row, f"DEL_m{exponent}")
                assert value == pytest.approx(calc_del(samples[row.case_row - 2][name], exponent, 100, method))
                assert getattr(row, f"DEL_1Hz_m{exponent}") == pytest.approx(value * (100 / row.duration_s) ** (1 / exponent))
    assert all(reader.ReadAll.call_count == 1 for reader in readers)


@pytest.mark.parametrize("timestamps", [None, [], [1], [1, 1], [2, 1], [0, np.nan],
                                       [0, np.inf], [[0, 1]], ["bad", "time"], [-1e308, 1e308]])
def test_invalid_reader_timestamps(fls_inputs, monkeypatch, timestamps):
    """Reject invalid time vectors with case and file context before counting.

    Parameters: fls_inputs supplies cases; monkeypatch replaces reader; timestamps supplies invalid input.
    Returns: None; invalid duration raises an actionable error and counting is skipped.
    Examples: pytest tests/test_fls.py -k invalid_reader
    """
    cases, samples = fls_inputs
    reader = Mock()
    reader.ReadAll.return_value = samples[0]
    reader.t = timestamps
    monkeypatch.setattr("load_arena.process.fls.ReadHawc2", Mock(return_value=reader))
    counting = Mock()
    monkeypatch.setattr("load_arena.process.fls.calculate_rainflow", counting)
    with pytest.raises(ValueError, match="CSV row 2.*simulation .*a.*[Tt]imestamp"):
        calc_fls(cases, [4], 100, channels=["load"])
    counting.assert_not_called()


def test_exponent_labels_and_new_api(fls_inputs):
    """Preserve precise exponent labels and expose only channel-based results.

    Parameters: fls_inputs supplies cases and sample readers.
    Returns: None; labels are ordered, distinct, and old fields are absent.
    Examples: pytest tests/test_fls.py -k exponent_labels
    """
    cases, _ = fls_inputs
    result = calc_fls(cases, [6, 4.000000000000001, 4, 2.5, 6], 100, "astm", channels=["load"])
    assert result.channels["load"].files.columns.tolist()[4:] == [
        "DEL_m6", "DEL_1Hz_m6", "DEL_m4.000000000000001", "DEL_1Hz_m4.000000000000001",
        "DEL_m4", "DEL_1Hz_m4", "DEL_m2.5", "DEL_1Hz_m2.5",
    ]
    for name in ("per_case", "campaign", "rainflow_results"):
        assert not hasattr(result, name)
