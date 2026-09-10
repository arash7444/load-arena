"""Occurrence-weighted campaign DELs built from the existing signal calculator."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from load_arena.case_loader.input_reader import validate_case_rows
from load_arena.data_reader.Hawc2io import ReadHawc2, toDataFrame
from load_arena.process.calc_del import calc_del
from load_arena.utils.channels import ChannelSelection, select_channels, validate_channels


@dataclass
class FLSResult:
    """Per-case and campaign DELs identified by channel and Wöhler exponent."""

    per_case: pd.DataFrame
    campaign: pd.DataFrame
    n_ref: float
    method: str


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
        Long-form per-case DELs and occurrence-weighted campaign DELs.
        Occurrences represents repetitions of the complete recorded simulation.

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
    rows = []
    for case_row, (_, case) in enumerate(cases.iterrows(), start=2):
        filename = (Path(case["Folder"]) / case["Timeseries"]).resolve()
        try:
            reader = ReadHawc2(filename)
            data = toDataFrame(reader.ReadAll(), reader.ChInfo)
        except Exception as exc:
            raise ValueError(f"FLS CSV row {case_row}, simulation {filename}: {exc}") from exc
        selected = select_channels(data, channels, f"FLS CSV row {case_row}, {filename}")
        for channel in selected.columns:
            for exponent in exponents:
                try:
                    value = calc_del(selected[channel], exponent, n_ref, method=method)
                    if not np.isfinite(value):
                        raise ValueError("DEL is not finite.")
                except (TypeError, ValueError, FloatingPointError) as exc:
                    raise ValueError(
                        f"FLS CSV row {case_row}, {filename}, channel {channel}, "
                        f"wohler_exponent {exponent}: {exc}"
                    ) from exc
                rows.append({
                    "case_row": case_row, "filename": str(filename), "channel": channel,
                    "wohler_exponent": exponent, "occurrences": float(case["Occurrences"]),
                    "DEL": value,
                })
    per_case = pd.DataFrame(rows)
    campaign_rows = []
    for (channel, exponent), group in per_case.groupby(["channel", "wohler_exponent"], sort=False):
        with np.errstate(over="raise", invalid="raise"):
            weighted = group.loc[group["occurrences"] > 0]
            damage = np.sum(weighted["occurrences"].to_numpy() * weighted["DEL"].to_numpy() ** exponent)
            value = float(damage ** (1.0 / exponent))
        campaign_rows.append({"channel": channel, "wohler_exponent": exponent, "DEL": value})
    return FLSResult(per_case, pd.DataFrame(campaign_rows), float(n_ref), method)
