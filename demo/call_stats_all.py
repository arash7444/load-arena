import seaborn as sns
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import pathlib as path
import os
import re
from rich.console import Console
from rich.traceback import install
from dataclasses import dataclass
install()
console = Console()


from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files
from load_arena.process.concatenate_stats import All_stats, concatenate_stats




list_files = find_files(folder_name = r".\tests\h2_res\dlc13", file_extension = ".int")
stats_hawc2 = concatenate_stats(list_files=list_files)

console.print(stats_hawc2.mean)

console.print(stats_hawc2.filename)

console.print(stats_hawc2.mean.columns)


fig, ax = plt.subplots(figsize=(10, 6))
plt.plot(stats_hawc2.mean.iloc[:,1], stats_hawc2.mean['Aerot._[kW]'], label='Mean Aerot. [kW]', color='blue', linestyle='', marker='o')
plt.grid()

plt.show()
