
from load_arena.process import calculate_rainflow, calc_del
from load_arena.data_reader import read_hawc2_flex, read_hawc2_sel
from load_arena.process.fatigue_results import make_rainflow_range_spectrum
from load_arena.visualization.fatigue_plots import plot_rainflow_range_spectrum
    
file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004" # hawc2 flex result file
    
data = read_hawc2_flex(file_flex) # Read flex result into data frame
    
spectrum = make_rainflow_range_spectrum(
        channel = data["blade1N1Mxcoo:_[kNm]"],
        bins=20,
    ) # Make rainflow range spectrum

fig = plot_rainflow_range_spectrum(spectrum) # Plot rainflow range spectrum
fig.show() # Show the plot

print("done")

