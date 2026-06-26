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
from load_arena.data_reader.Hawc2io import toDataFrame
from load_arena.utils import find_files

# @dataclass
# class SimpleStatsResult:
#     mean: pd.DataFrame
#     std: pd.DataFrame
#     min: pd.DataFrame
#     max: pd.DataFrame
#     filename: str




def calc_stats(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Calculate simple statistics (mean, std, min, max) for a given data of a file.

    Parameters:
    -----------
        df:pd.DataFrame
            Input DataFrame containing numerical data.

    Returns:
    --------
        stat_mean: pd.DataFrame
            DataFrame containing the mean of each column.
        stat_std: pd.DataFrame
            DataFrame containing the standard deviation of each column.
        stat_min: pd.DataFrame
            DataFrame containing the minimum value of each column.
        stat_max: pd.DataFrame
            DataFrame containing the maximum value of each column.

    Example:
    --------
        >>> df = pd.DataFrame({
        ...     'A': [1, 2, 3],
        ...     'B': [4, 5, 6]
        ... })
        >>> stat_mean, stat_std, stat_min, stat_max = calc_stats(df)
        >>> print(stat_mean)
           A    B
        0  2.0  5.0
        >>> print(stat_std)
           A    B
        0  1.0  1.0
        >>> print(stat_min)
           A    B
        0  1.0  4.0
        >>> print(stat_max)
           A    B
        0  3.0  6.0

    """
        
    # config = LoadArenaConfig(
    #     sims_path = path.Path(
    #         r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    #     ))
    # res_file = ReadHawc2(config.sims_path)
    # data = res_file.ReadAll()
    # res_file = ReadHawc2(config.sims_path)
    # data = res_file.ReadAll()

    # info = res_file.ChInfo
    # df = toDataFrame(data, info)



    stat_mean = df.mean(numeric_only=True).to_frame().T
    stat_std = df.std(numeric_only=True).to_frame().T
    stat_min = df.min(numeric_only=True).to_frame().T
    stat_max = df.max(numeric_only=True).to_frame().T

    # console.print(simple_stats.mean)

    return stat_mean, stat_std, stat_min, stat_max




# if __name__ == "__main__":

#     list_files = find_files(folder_name = r".\tests\h2_res\dlc13", file_extension = ".int")

#     all_stats = All_stats(
#         mean=pd.DataFrame(),
#         std=pd.DataFrame(),
#         min=pd.DataFrame(),
#         max=pd.DataFrame(),
#         filename=[]
#     )
#     for file in list_files:
#         config = LoadArenaConfig(
#             sims_path=file
#         )
#         res_file = ReadHawc2(config.sims_path)
#         data = res_file.ReadAll()
#         info = res_file.ChInfo
#         df = toDataFrame(data, info)

#         stat_mean, stat_std, stat_min, stat_max = calc_stats(df)

#         # for pd.concat() only concatenates pandas objects, not dataclass objects.
#         # so we need to concatenate the individual DataFrames within the dataclass.
#         all_stats.mean = pd.concat(
#             [all_stats.mean, stat_mean],
#             ignore_index=True,
#         )

#         all_stats.std = pd.concat(
#             [all_stats.std, stat_std],
#             ignore_index=True,
#         )

#         all_stats.min = pd.concat(
#             [all_stats.min, stat_min],
#             ignore_index=True,
#         )

#         all_stats.max = pd.concat(
#             [all_stats.max, stat_max],
#             ignore_index=True,
#         )
#     all_files = [file.name for file in list_files]
#     all_stats.filename = all_files



        
#     # simple_stats = calc_stats(pd.DataFrame())
#     console.print(all_stats.mean)

#     console.print(all_stats.filename)
