import seaborn as sns
import matplotlib.pyplot as plt

import pandas as pd
import pathlib as path
import os
import re
from rich.console import Console
from rich.traceback import install

install()
console = Console()


from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files
from load_arena.process.concatenate_stats import All_stats, concatenate_stats
from load_arena.case_loader import read_uls_input_file


# # # use a simple way: just provide the folder name and extension or read from input file
# list_files = find_files(folder_name=r".\tests\h2_res\dlc13", file_extension=".int")

file_name = r".\tests\input_file\ULS_input_file.csv"
df_input = read_uls_input_file(file_name)
# list_files = df_input["Folder"] + df_input["Timeseries"]

all_stats_hawc2 = concatenate_stats(input_file_df=df_input)

console.print(all_stats_hawc2.mean)

console.print(all_stats_hawc2.filename)

console.print(all_stats_hawc2.mean.columns)


fig, ax = plt.subplots(figsize=(10, 6))
plt.plot(
    all_stats_hawc2.mean.iloc[:, 1],
    all_stats_hawc2.mean["Aerot._[kW]"],
    label="Mean Aerot. [kW]",
    color="blue",
    linestyle="",
    marker="o",
)
plt.grid()

plt.show(block=False)

console.print("----------------------------------")

input("Press Enter to exit")

console.print("mean: \n",all_stats_hawc2.mean["Aerot._[kW]"])

console.print("----------------------------------")

console.print("mean_plf: \n",all_stats_hawc2.mean_plf["Aerot._[kW]"])
plt.close()
