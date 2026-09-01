from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd

from load_arena.process.rainflowcount import rainflow_astm, rainflow_windap


@dataclass
class RainflowResult:
    """
    Store rainflow cycles and the parameters used to calculate them.
    """

    cycles: pd.DataFrame
    method: str
    levels: int | None = None
    threshold: float | None = None

    @property
    def range(self) -> pd.Series:
        """
        Return the range of each counted half-cycle.

        Returns
        -------
        pandas.Series
            Cycle ranges from the result table.
        """
        return self.cycles["range"]

    @property
    def mean(self) -> pd.Series:
        """
        Return the mean load of each counted half-cycle.

        Returns
        -------
        pandas.Series
            Cycle means from the result table.
        """
        return self.cycles["mean"]

    @property
    def count(self) -> pd.Series:
        """
        Return the count assigned to each rainflow half-cycle.

        Returns
        -------
        pandas.Series
            Half-cycle counts from the result table.
        """
        return self.cycles["count"]


def calculate_rainflow(
    signal: np.ndarray | pd.Series,
    method: str = "windap",
    levels: int = 255,
    threshold: float = 255 / 50,
) -> RainflowResult:
    """Calculate rainflow half-cycles from a finite one-dimensional signal.

    Parameters
    ----------
    signal : numpy.ndarray or pandas.Series
        Finite one-dimensional load signal to analyze.
    method : {"windap", "astm"}, default "windap"
        Rainflow counting method.
    levels : int, default 255
        Positive number of Windap discretization levels.
    threshold : float, default 255 / 50
        Positive Windap peak-trough threshold in discretized levels.

    Returns
    -------
    RainflowResult
        Independent result containing cycle ranges, means, counts

    Examples
    --------
    >>> signal = np.array([-2.0, 0.0, 1.0, 0.0, -3.0])
    >>> result = calculate_rainflow(signal, method="astm")
    >>> result.cycles.columns.tolist()
    ['range', 'mean', 'count']
    """
    if isinstance(signal, pd.Series):
        try:
            values = signal.to_numpy(dtype=float, na_value=np.nan)
        except (TypeError, ValueError) as exc:
            raise TypeError("Rainflow signal must contain numeric values.") from exc
    else:
        try:
            values = np.asarray(signal, dtype=float)
        except (TypeError, ValueError) as exc:
            raise TypeError("Rainflow signal must contain numeric values.") from exc

    if values.ndim != 1:
        raise ValueError("Rainflow signal must be one-dimensional.")
    if values.size == 0:
        raise ValueError("Rainflow signal must contain at least one value.")
    if not np.all(np.isfinite(values)):
        raise ValueError("Rainflow signal must contain only finite values.")
    if method not in {"windap", "astm"}:
        raise ValueError(f"Unknown rainflow method: {method}")

    if method == "windap":
        if isinstance(levels, (bool, np.bool_)) or not isinstance(
            levels, (int, np.integer)
        ):
            raise TypeError("Windap levels must be a positive integer.")
        if levels <= 0:
            raise ValueError("Windap levels must be a positive integer.")
        if isinstance(threshold, (bool, np.bool_)) or not isinstance(
            threshold, (int, float, np.integer, np.floating)
        ):
            raise TypeError("Windap threshold must be a positive finite number.")
        if not np.isfinite(threshold) or threshold <= 0:
            raise ValueError("Windap threshold must be a positive finite number.")
        result_levels: int | None = int(levels)
        result_threshold: float | None = float(threshold)
    else:
        result_levels = None
        result_threshold = None

    if np.min(values) == np.max(values):
        warnings.warn(
            "Rainflow signal contains no variation; returning zero cycles.",
            RuntimeWarning,
            stacklevel=2,
        )
        return RainflowResult(
            cycles=pd.DataFrame(
                {
                    "range": pd.Series(dtype=float),
                    "mean": pd.Series(dtype=float),
                    "count": pd.Series(dtype=float),
                }
            ),
            method=method,
            levels=result_levels,
            threshold=result_threshold,
        )

    if method == "windap":
        ranges, means = rainflow_windap(
            values,
            levels=result_levels,
            thresshold=result_threshold,
        )
    else:
        ranges, means = rainflow_astm(values)

    ranges = np.asarray(ranges, dtype=float)
    means = np.asarray(means, dtype=float)
    positive_range = ranges > 0
    cycles = pd.DataFrame(
        {
            "range": ranges[positive_range],
            "mean": means[positive_range],
            "count": np.full(np.count_nonzero(positive_range), 0.5, dtype=float),
        }
    )
    return RainflowResult(
        cycles=cycles,
        method=method,
        levels=result_levels,
        threshold=result_threshold,
    )
