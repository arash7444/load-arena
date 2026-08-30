import plotly.graph_objects as go

from load_arena.process.fatigue_results import RainflowRangeSpectrum
from load_arena.data_reader import read_hawc2_flex
from load_arena.process.fatigue_results import make_rainflow_range_spectrum


def plot_rainflow_range_spectrum(
    spectrum: RainflowRangeSpectrum,
) -> go.Figure:

    fig = go.Figure()

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

if __name__ == "__main__":
    
    file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    
    data = read_hawc2_flex(file_flex)
    
    spectrum = make_rainflow_range_spectrum(
        channel = data["blade1N1Mxcoo:_[kNm]"],
        bins=20,
    )
    
    fig = plot_rainflow_range_spectrum(spectrum)
    fig.show()

    print("done")