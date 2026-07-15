import matplotlib.pyplot as plt
from rich.console import Console
from rich.traceback import install

from load_arena.data_reader import  Hawc2io, toDataFrame, LoadArenaConfig
from load_arena.process.concatenate_stats import concatenate_stats

from load_arena.process import calculate_rainflow, calc_del
from load_arena.data_reader import read_hawc2_flex, read_hawc2_sel


install()
console = Console()
file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"

data = read_hawc2_flex(file_flex)

RainflowResult = calculate_rainflow(data["blade1N1Mxcoo:_[kNm]"], method="windap")
console.print("Rainflow counts (range, mean, count): ",RainflowResult.range, RainflowResult.mean, RainflowResult.count)

DEL_1hz = calc_del(
    data["blade1N1Mxcoo:_[kNm]"],
    wohler_exponent=10,
    n_ref=600,
    method="windap",
)

console.print("1 Hz DEL: ", DEL_1hz)



