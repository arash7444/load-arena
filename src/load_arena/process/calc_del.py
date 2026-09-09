import plotly.graph_objects as go

from PIL import ImageColor
import numpy as np
import pandas as pd
from dataclasses import dataclass
from load_arena.process.calculate_rainflow import RainflowResult, calculate_rainflow
from rich.console import Console
from rich.markdown import Markdown

 

console = Console()

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
        reference cycle number. 
        for example, 600 for 1 Hz. for 10 minutes simulation
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
    >>> calc_del(signal, wohler_exponent=4, n_ref=600, method="astm")
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
    damage_sum = np.sum(counts * ranges**float(wohler_exponent)) # Damage integral for all ranges
    del_val = float((damage_sum / float(n_ref)) ** (1.0 / float(wohler_exponent))) # Damage equivalent load
    
    return del_val

@dataclass
class DamageRangeSpectrum:
    range_center: np.ndarray
    damage: np.ndarray

def make_damage_range_spectrum(
    cycles: RainflowResult,
    wohler_exponent: float,
    bins: int = 20,
) -> DamageRangeSpectrum:
    """
    Calculate the damage equivalent for each range of the rainflow spectrum.
    for example, if we have 100 cycles of range 2, and we want to plot the damage range spectrum, 
    we will have a bar at range 2 with height of 100 * 2**wohler_exponent.

    Parameters
    ----------
    cycles : RainflowResult
        Rainflow result.
    wohler_exponent : float
            Positive finite Wohler exponent used by the damage model.
        bins : int, default 20
            Number of bins to use for the histogram.

        Returns
        -------
        DamageRangeSpectrum
            Damage range spectrum.

        Example
        -------
        >>> cycles = calculate_rainflow(np.array([0.0, 2.0, 0.0]))
        >>> damage_spectrum = make_damage_range_spectrum(cycles, wohler_exponent=4)
    """
    ranges = cycles.range.to_numpy(dtype=float)
    counts = cycles.count.to_numpy(dtype=float)

    # damage_per_cycle = counts * ranges**wohler_exponent # Damage per range
    damage_contribution = counts * ranges**wohler_exponent # Damage contribution of each range
    bin_edges = np.linspace(
        0,
        ranges.max(),
        bins + 1,
    )

    damage, bin_edges = np.histogram(
        ranges,
        bins=bin_edges,
        weights=damage_contribution,
    )

    range_center = (bin_edges[:-1] + bin_edges[1:]) / 2

    return DamageRangeSpectrum(
        range_center=range_center,
        damage=damage,
    )

def damage_fraction(
    damage: DamageRangeSpectrum,
):
    """
    Calculate the damage fraction of each range of the rainflow spectrum.

    Parameters
    ----------
    damage : DamageRangeSpectrum
        Damage range spectrum.

    Returns
    -------
    np.ndarray, np.ndarray
        Damage fraction and damage percentage.
    """
    # damage contribution as percentage of total damage:
    damage_fraction = (
    damage.damage
    / damage.damage.sum()
    )

    damage_percent = (damage_fraction * 100).round(2)
    # console.print(Markdown("Damage fraction (%):"))
    # console.print(damage_percent)
    return damage_fraction, damage_percent

if __name__ == "__main__":

    from load_arena.case_loader import read_fls_input_file
    from load_arena.data_reader import read_hawc2_flex
    from load_arena.utils import find_files
    from load_arena.process import calculate_rainflow
    
    
    file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    data = read_hawc2_flex(file_flex)
    wohlmer_m = 10.0
    channel = "towerN27Mycoo:_[kNm]" #"shaftN4Mxcoo:_[kNm]" #"blade1N1Mxcoo:_[kNm]"
    RainflowResult = calculate_rainflow(data[channel], method="windap")
 
    

    # Calculate the damage equivalent for each range of the rainflow spectrum:
    damage_spectrum = make_damage_range_spectrum(
    RainflowResult,
    wohler_exponent=wohlmer_m,
    bins=20,
    )


    console.print("Damage Range Spectrum:")
    console.print(damage_spectrum.range_center)
    console.print("----------------------------------------------------------------")

    console.print("Damage:")
    console.print(damage_spectrum.damage)
    console.print("----------------------------------------------------------------")



    # # damage contribution as percentage of total damage:
    # damage_fraction = (
    # damage_spectrum.damage
    # / damage_spectrum.damage.sum()
    # )
    # damage_percent = (damage_fraction * 100).round(2)

    damage_fraction, damage_percent = damage_fraction(damage_spectrum)

    console.print(Markdown("Damage fraction (%):"))
    console.print(damage_percent)
    console.print("----------------------------------------------------------------")



    # Calculate the total damage from the damage range spectrum (to compare with the value from calc_del)
    total_damage_from_spectrum = damage_spectrum.damage.sum()
    
    del_from_spectrum = (
        total_damage_from_spectrum / 600
    ) ** (1 / wohlmer_m)


    console.print("DEL from damage spectrum:")
    console.print(del_from_spectrum)    
    console.print("----------------------------------------------------------------")


    # Calculate the damage equivalent load directly from the signal: 
    del_val = calc_del(
        signal=data[channel],
        wohler_exponent=wohlmer_m,
        n_ref=600,
        method="windap",
    )

    console.print("Damage Equivalent Load:")
    console.print(del_val)
    console.print("----------------------------------------------------------------")



    fig = go.Figure()

    fig.add_bar(
        x=damage_spectrum.range_center,
        y=damage_spectrum.damage,
    )

    fig.update_layout(
        title="Damage Range Spectrum",
        xaxis_title="Load Range",
        yaxis_title="Damage Contribution",
    )

    fig2 = go.Figure()

    fig2.add_bar(
        x=damage_spectrum.range_center,
        y=damage_percent
    )

    fig2.update_layout(
        title="Damage Percentage",
        xaxis_title="Load Range",
        yaxis_title="Damage Percentage",
    )

  
    fig.show()
    fig2.show()



    