import numpy as np
import pandas as pd

from load_arena.process.calculate_rainflow import calculate_rainflow


def calc_del(
    signal: np.ndarray | pd.Series,
    wohler_exponent: float,
    n_ref: float,
    method: str = "windap",
    levels: int = 255,
    threshold: float = 255 / 50,
) -> float:
    """Calculate the damage-equivalent load of a raw load signal.

    Parameters
    ----------
    signal : numpy.ndarray or pandas.Series
        Finite one-dimensional load signal.
    wohler_exponent : float
        Positive finite Wohler exponent used by the damage model.
    n_ref : float
        Positive finite reference cycle count.
    method : {"windap", "astm"}, default "windap"
        Rainflow counting method.
    levels : int, default 255
        Windap discretization levels; ignored for ASTM.
    threshold : float, default 255 / 50
        Windap peak-trough threshold; ignored for ASTM.

    Returns
    -------
    float
        Damage-equivalent load, or zero when the signal has no cycles.

    Examples
    --------
    >>> signal = np.array([0.0, 2.0, 0.0])
    >>> calc_del(signal, wohler_exponent=4, n_ref=1, method="astm")
    2.0
    """
    if isinstance(wohler_exponent, (bool, np.bool_)) or not isinstance(
        wohler_exponent, (int, float, np.integer, np.floating)
    ):
        raise TypeError("wohler_exponent must be a positive finite number.")
    if not np.isfinite(wohler_exponent) or wohler_exponent <= 0:
        raise ValueError("wohler_exponent must be a positive finite number.")
    if isinstance(n_ref, (bool, np.bool_)) or not isinstance(
        n_ref, (int, float, np.integer, np.floating)
    ):
        raise TypeError("n_ref must be a positive finite number.")
    if not np.isfinite(n_ref) or n_ref <= 0:
        raise ValueError("n_ref must be a positive finite number.")

    cycles = calculate_rainflow(
        signal,
        method=method,
        levels=levels,
        threshold=threshold,
    )
    if cycles.cycles.empty:
        return 0.0

    ranges = cycles.range.to_numpy(dtype=float)
    counts = cycles.count.to_numpy(dtype=float)
    damage_sum = np.sum(counts * ranges**float(wohler_exponent))
    return float((damage_sum / float(n_ref)) ** (1.0 / float(wohler_exponent)))
