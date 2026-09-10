from rich.console import Console

console = Console()
import plotly.graph_objects as go

from load_arena.data_reader import read_hawc2_flex
from load_arena.process.calc_del import make_damage_range_spectrum, damage_fraction, calc_del, DamageRangeSpectrum
from load_arena.process.calculate_rainflow import RainflowResult, calculate_rainflow
import pandas as pd
from load_arena.process.fatigue_results import make_rainflow_range_spectrum, RainflowRangeSpectrum, make_rainflow_matrix, RainflowMatrix


def plot_rainflow_range_spectrum(
    data: pd.Series,
) -> go.Figure:

    fig = go.Figure()
    spectrum = make_rainflow_range_spectrum(
        data,
        bins=20,
    )

    fig.add_bar(
        x=spectrum.range_center,
        y=spectrum.count,
    )

    fig.update_layout(
        title="Rainflow Range Spectrum",
        xaxis_title="Load Range",
        yaxis_title="Cycle Count",
    )

    return fig


def plot_damage_ratio(damage_spectrum,damage_percent):


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

    return fig2


import plotly.graph_objects as go

from load_arena.process.fatigue_results import RainflowMatrix
import numpy as np

def plot_rainflow_matrix(
    rainflow_matrix: RainflowMatrix,
) -> go.Figure:

    z = rainflow_matrix.count.T.copy()
    z[z == 0] = np.nan # set zero to NaN to hide the zero values in the heatmap

    fig = go.Figure(
        data=go.Heatmap(
            x=rainflow_matrix.mean_center,
            y=rainflow_matrix.range_center,
            z=z,
            colorbar_title="Cycle Count",
        )
    )

    fig.update_layout(
        title="Rainflow Matrix",
        xaxis_title="Mean Load",
        yaxis_title="Cycle Range",
    )

    return fig

if __name__ == "__main__":
    
    file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    
    data = read_hawc2_flex(file_flex)
    channel = "blade1N1Mxcoo:_[kNm]"

    fig = plot_rainflow_range_spectrum(data[channel])
    fig.show()


    RainflowResult = calculate_rainflow(data[channel], method="windap")

    damage_spectrum = make_damage_range_spectrum(
        RainflowResult,
        wohler_exponent=10,
        bins=20,
    )
    damage_fraction, damage_percent = damage_fraction(damage_spectrum)
    fig2 = plot_damage_ratio(damage_spectrum,damage_percent)
    fig2.show()



    spectrum = make_rainflow_range_spectrum(
        channel = data["blade1N1Mxcoo:_[kNm]"],
        bins=20,
    )





    # 2D matrix
    rainflow_matrix = make_rainflow_matrix(
    RainflowResult,
    mean_bins=20,
    range_bins=20,
    )
    print("----------------------------------------------------------------")
    console.print(("Rainflow Matrix:"))
    console.print(rainflow_matrix.mean_center)
    console.print(rainflow_matrix.range_center)
    console.print(rainflow_matrix.count)    
    print("----------------------------------------------------------------")

    fig3 = plot_rainflow_matrix(rainflow_matrix)
    fig3.show()




    print("done")
