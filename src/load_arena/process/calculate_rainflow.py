from dataclasses import dataclass

import numpy as np
import pandas as pd
from load_arena.process import (
    rainflow_astm,
    rainflow_windap,
)


@dataclass
class RainflowResult:
    cycles: pd.DataFrame
    method: str
    levels: int | None = None
    threshold: float | None = None


def calculate_rainflow(
    signal: np.ndarray,
    method: str = "windap",
    levels: int = 255,
    threshold: float = 255 / 50,
) -> RainflowResult:
    """Calculate rainflow cycles from a 1D signal.

    Supports both 'windap' and 'astm' rainflow counting methods.

    Parameters
    ----------
    signal : np.ndarray
        The 1D signal to analyze.
    method : str, default "windap"
        The rainflow counting method to use. Must be either "windap" or "astm".
    levels : int, default 255
        The number of discrete levels to use for discretization. Only applicable
        when method is "windap".
    threshold : float, default 255 / 50
        Cycles with range smaller than this threshold are ignored. Only applicable
        when method is "windap".

    Returns
    -------
    RainflowResult
        An object containing the resulting cycles as a DataFrame, the method used,
        and the parameters applied.

    Examples
    --------
    >>> signal = np.array([-2.0, 0.0, 1.0, 0.0, -3.0, 0.0, 5.0, 0.0])
    >>> result = calculate_rainflow(signal, method="windap")
    """
    signal = np.asarray(signal, dtype=float)

    if signal.ndim != 1:
        raise ValueError("Rainflow signal must be one-dimensional.")

    if np.all(np.isnan(signal)):
        raise ValueError("Rainflow signal contains only NaN values.")

    signal = signal[~np.isnan(signal)]

    if np.min(signal) == np.max(signal):
        raise ValueError("Rainflow signal contains no variation.")

    if method == "windap":
        ranges, means = rainflow_windap(
            signal,
            levels=levels,
            thresshold=threshold,
        )
    elif method == "astm":
        ranges, means = rainflow_astm(signal)
        levels = None
        threshold = None
    else:
        raise ValueError(f"Unknown rainflow method: {method}")

    RainflowResult = pd.DataFrame(
        {
            "range": ranges,
            "mean": means,
            "count": np.full(len(ranges), 0.5),
        }
    )

    return RainflowResult