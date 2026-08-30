import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import numpy as np
from rich.console import Console
from rich.markdown import Markdown
from rich.traceback import install
console = Console()

from load_arena.data_reader import  Hawc2io, toDataFrame, LoadArenaConfig
from load_arena.process.concatenate_stats import concatenate_stats

from load_arena.process import calculate_rainflow, calc_del
from load_arena.data_reader import read_hawc2_flex, read_hawc2_sel
from dataclasses import dataclass

@dataclass
class RainflowRangeSpectrum:
    """
    Class to store the rainflow range spectrum.

    Attributes
    ----------
    range_center : np.ndarray
        Center of the rainflow ranges.
    count : np.ndarray
        Count of the rainflow ranges.
    mean_val : float
        Mean value of the rainflow ranges.
    """
    range_center: np.ndarray
    count: np.ndarray
    mean_val: float


def make_rainflow_range_spectrum(
    channel: pd.Series,
    bins: int = 20,
) -> RainflowRangeSpectrum:
    """
    Calculate the rainflow range spectrum of a channel.

    Parameters
    ----------
    channel : pd.Series
        Channel to calculate the rainflow range spectrum of.
    bins : int
        Number of bins to use for the histogram.

    Returns
    -------
    RainflowRangeSpectrum
        Rainflow range spectrum.

    Example
    -------
    >>> file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    >>> data = read_hawc2_flex(file_flex)
    >>> result = make_rainflow_range_spectrum(data["blade1N1Mxcoo:_[kNm]"])
    >>> console.print(result)
    """

    RainflowResult = calculate_rainflow(channel, method="windap")

    console.print(RainflowResult)

    ranges = RainflowResult.range.to_numpy(dtype=float)
    counts = RainflowResult.count.to_numpy(dtype=float)
    mean_val = RainflowResult.mean.to_numpy(dtype=float)

    bin_edges = np.linspace(
        0,
        ranges.max(),
        bins + 1,
    ) # 

    histogram, bin_edges = np.histogram(
        ranges,
        bins=bin_edges,
        weights=counts,
    )

    range_center = (bin_edges[:-1] + bin_edges[1:]) / 2

    return RainflowRangeSpectrum(
        range_center=range_center,
        count=histogram,
        mean_val=mean_val,
    )   

if __name__ == "__main__":
    
    file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"

    data = read_hawc2_flex(file_flex)

    result = make_rainflow_range_spectrum(data["blade1N1Mxcoo:_[kNm]"])
    console.print(result)

