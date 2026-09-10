"""Occurrence-weighted campaign DELs built from the existing signal calculator."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from load_arena.case_loader.input_reader import validate_case_rows
from load_arena.data_reader.Hawc2io import ReadHawc2, toDataFrame
from load_arena.process.calc_del import calc_del_from_rainflow
from load_arena.process.calculate_rainflow import RainflowResult, calculate_rainflow
from load_arena.utils.channels import ChannelSelection, select_channels, validate_channels


@dataclass
class FLSChannelResult:
    """Store wide file DELs, cycles keyed by CSV row, and campaign DELs."""

    files: pd.DataFrame
    rainflow_results: dict[int, RainflowResult]
    campaign: pd.DataFrame


@dataclass
class FLSResult:
    """Store channel results in selection order and shared fatigue parameters."""

    channels: dict[str, FLSChannelResult]
    n_ref: float
    method: str


def _simulation_duration(timestamps: object) -> float:
    """Return the elapsed seconds between the first and last reader timestamps.

    Parameters
    ----------
    timestamps : object
        Reader time vector in seconds, with at least two finite increasing values.

    Returns
    -------
    float
        Positive finite timestamp span; invalid input raises ValueError.

    Examples
    --------
    >>> _simulation_duration([10., 11., 12.])
    2.0
    """
    try:
        times = np.asarray(timestamps, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Simulation timestamps must be numeric.") from exc
    if times.ndim != 1 or times.size < 2 or not np.all(np.isfinite(times)):
        raise ValueError("Simulation timestamps must contain at least two finite values.")
    if not np.all(times[1:] > times[:-1]):
        raise ValueError("Simulation timestamps must be strictly increasing.")
    with np.errstate(over="ignore"):
        duration = float(times[-1] - times[0])
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("Simulation timestamp span must be positive and finite.")
    return duration


def calc_fls(
    cases: pd.DataFrame,
    wohler_exponents: list[float],
    n_ref: float,
    method: str = "windap",
    *,
    channels: ChannelSelection,
) -> FLSResult:
    """Calculate DELs for selected channels and shared Wöhler exponents.

    Parameters
    ----------
    cases : pandas.DataFrame
        Validated FLS cases with Folder, Timeseries, and Occurrences columns.
    wohler_exponents : list[float]
        Positive finite exponents applied to every selected channel.
    n_ref : float
        Positive reference cycle count shared by every case and channel.
    method : {"windap", "astm"}, default "windap"
        Existing rainflow counting method.
    channels : list[str] or {"all"}
        Nonempty, unique names present in every case, or all simulation channels.

    Returns
    -------
    FLSResult
        Channel-indexed wide file tables, retained cycles, and campaign DELs.
        Occurrences represents repetitions of the complete recorded simulation.
        Per-case duration_s is the reader timestamp span in seconds and supplies
        the reference count for DEL_1Hz. Full rainflow results are retained once
        per case/channel and reused across exponents and reference counts.

    Examples
    --------
    >>> result = calc_fls(cases, [4, 10], 1e7, channels=["Load_[kN]"])
    """
    validate_case_rows(cases, "fls")
    if channels != "all":
        validate_channels(channels)
    if not isinstance(wohler_exponents, list) or not wohler_exponents:
        raise ValueError("wohler_exponents must be a nonempty list.")
    for name, values in (("wohler_exponents", wohler_exponents), ("n_ref", [n_ref])):
        for value in values:
            if (isinstance(value, (bool, np.bool_)) or
                    not isinstance(value, (int, float, np.integer, np.floating)) or
                    not np.isfinite(value) or value <= 0):
                raise ValueError(f"{name} must contain positive finite numbers.")
    if method not in {"windap", "astm"}:
        raise ValueError(f"Unknown rainflow method: {method}")
    # Repeating an exponent must not double-count its damage contributions.
    exponents = list(dict.fromkeys(float(value) for value in wohler_exponents))
    rows = {}
    rainflow_results = {}
    labels = [repr(m).removesuffix(".0") for m in exponents]
    for case_row, (_, case) in enumerate(cases.iterrows(), start=2):
        filename = (Path(case["Folder"]) / case["Timeseries"]).resolve()
        try:
            reader = ReadHawc2(filename)
            data = toDataFrame(reader.ReadAll(), reader.ChInfo)
            duration_s = _simulation_duration(reader.t)
        except Exception as exc:
            raise ValueError(f"FLS CSV row {case_row}, simulation {filename}: {exc}") from exc
        selected = select_channels(data, channels, f"FLS CSV row {case_row}, {filename}")
        for channel in selected.columns:
            try:
                cycles = calculate_rainflow(selected[channel], method=method)
            except (TypeError, ValueError, FloatingPointError) as exc:
                raise ValueError(
                    f"FLS CSV row {case_row}, {filename}, channel {channel}: {exc}"
                ) from exc
            rainflow_results.setdefault(channel, {})[case_row] = cycles
            row = {"case_row": case_row, "filename": str(filename),
                   "occurrences": float(case["Occurrences"]), "duration_s": duration_s}
            for exponent, label in zip(exponents, labels):
                try:
                    value = calc_del_from_rainflow(cycles, exponent, n_ref)
                    value_1hz = calc_del_from_rainflow(cycles, exponent, duration_s)
                    if not np.isfinite(value) or not np.isfinite(value_1hz):
                        raise ValueError("DEL is not finite.")
                except (TypeError, ValueError, FloatingPointError) as exc:
                    raise ValueError(
                        f"FLS CSV row {case_row}, {filename}, channel {channel}, "
                        f"wohler_exponent {exponent}: {exc}"
                    ) from exc
                row[f"DEL_m{label}"] = value
                row[f"DEL_1Hz_m{label}"] = value_1hz
            rows.setdefault(channel, []).append(row)
    channel_results = {}
    for channel, records in rows.items():
        files = pd.DataFrame(records)
        campaign_rows = []
        for exponent, label in zip(exponents, labels):
            with np.errstate(over="raise", invalid="raise"):
                weighted = files.loc[files["occurrences"] > 0]
                damage = np.sum(weighted["occurrences"].to_numpy() * weighted[f"DEL_m{label}"].to_numpy() ** exponent)
                value = float(damage ** (1.0 / exponent))
            campaign_rows.append({"wohler_exponent": exponent, "DEL": value})
        channel_results[channel] = FLSChannelResult(
            files, rainflow_results[channel], pd.DataFrame(campaign_rows),
        )
    return FLSResult(channel_results, float(n_ref), method)
