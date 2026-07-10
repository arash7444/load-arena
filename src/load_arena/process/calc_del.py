from signal import signal
import numpy as np
import pandas as pd


import matplotlib.pyplot as plt
from rich.console import Console
from rich.traceback import install

from load_arena.data_reader import  Hawc2io, toDataFrame, LoadArenaConfig
from load_arena.process.concatenate_stats import concatenate_stats

from load_arena.process import calculate_rainflow
from load_arena.data_reader import read_hawc2_flex, read_hawc2_sel

install()
console = Console()

def calc_del(
    cycles: pd.DataFrame,
    wohler_exponent: float,
    n_ref: float,
) -> float:
    '''
    Calculates the fatigue damage equivalent load from rainflow cycles.

    Parameters
    ----------
    cycles : pd.DataFrame
        DataFrame containing the rainflow results including range, mean and cycle number (half-cycles).
    wohler_exponent : float
        The Wohler exponent.
    n_ref : float
        The reference life.

    Returns
    -------
    float
        The damage equivalent load.

    Examples
    --------
    >>> del = calc_del(cycles, wohler_exponent, n_ref)
    
    '''

    ranges = cycles.range
    counts = cycles.count

    damage_sum = np.sum(counts * ranges**wohler_exponent)

    del_val = (damage_sum / n_ref) ** (1.0 / wohler_exponent)

    return del_val


if __name__ == "__main__":



    file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"

    data = read_hawc2_flex(file_flex)
    signal = data["blade1N1Mxcoo:_[kNm]"]

    rf_result_windap = calculate_rainflow(signal, method="windap")
    rf_result_astm = calculate_rainflow(signal, method="astm")

    del_1hz_windap = calc_del(
        cycles=rf_result_windap,
        wohler_exponent=10,
        n_ref=data["Time_[s]"].iloc[-1] - data["Time_[s]"].iloc[0],
    )    
    del_1hz_astm = calc_del(
        cycles=rf_result_astm,
        wohler_exponent=10,
        n_ref=data["Time_[s]"].iloc[-1] - data["Time_[s]"].iloc[0],
    )    
        

    console.print(f"DEL windap: {del_1hz_windap}")
    console.print(f"DEL astm: {del_1hz_astm}")
    console.print(f"std: {data['blade1N1Mxcoo:_[kNm]'].std()}")
