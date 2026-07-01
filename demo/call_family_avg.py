
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
from load_arena.case_loader import read_input_file
from load_arena.process.family_avg import FamilyAvg, calc_family_avg



file_name = r".\tests\input_file\input_file.csv"
df_input = read_input_file(file_name)
list_files = df_input["Folder"] + df_input["Timeseries"]

all_stats_hawc2 = concatenate_stats(input_file_df=df_input)

family_stats = calc_family_avg(all_stats_hawc2, df_input)


console.print("Family average mean: \n",family_stats.mean)
console.print("Family average  std: \n",family_stats.std)
console.print("Family average min: \n",family_stats.min)
console.print("Family average max: \n",family_stats.max)
console.print("Family average filename: \n",family_stats.filename)
console.print("Family average family_name: \n",family_stats.family_name)