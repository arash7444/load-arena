import pandas as pd
from dataclasses import dataclass
from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
import os
from rich.console import Console
from rich.traceback import install

install()
console = Console()


@dataclass
class All_stats:
    mean: pd.DataFrame
    std: pd.DataFrame
    min: pd.DataFrame
    max: pd.DataFrame
    filename: str
    family: str


def concatenate_stats(input_file_df: list | pd.DataFrame) -> pd.DataFrame:
    """
    Concatenate a list of All_stats objects into a single DataFrame.

    Parameters:
    -----------
        list_files: list
            A list of file paths corresponding to the statistics or  a Dataframe from input file

    Returns:
    --------
        all_stats: dataclass
            A dataclass object containing the concatenated statistics from all All_stats objects.
    """

    all_stats = All_stats(
        mean=pd.DataFrame(),
        std=pd.DataFrame(),
        min=pd.DataFrame(),
        max=pd.DataFrame(),
        filename=[],
        family=[],
    )


    # if list_files is a DataFrame, extract the file paths
    if isinstance(input_file_df, pd.DataFrame): 
        list_files = input_file_df["Folder"] + input_file_df["Timeseries"]
    else:
        list_files = input_file_df

    for file in list_files:
        # print(type(file))

        config = LoadArenaConfig(sims_path=file)
        res_file = ReadHawc2(config.sims_path)
        data = res_file.ReadAll()
        info = res_file.ChInfo
        df = toDataFrame(data, info)

        stat_mean, stat_std, stat_min, stat_max = calc_stats(df)

        ## for pd.concat() only concatenates pandas objects, not dataclass objects.
        ## so we need to concatenate the individual DataFrames within the dataclass.
        all_stats.mean = pd.concat(
            [all_stats.mean, stat_mean],
            ignore_index=True,
        )

        all_stats.std = pd.concat(
            [all_stats.std, stat_std],
            ignore_index=True,
        )

        all_stats.min = pd.concat(
            [all_stats.min, stat_min],
            ignore_index=True,
        )

        all_stats.max = pd.concat(
            [all_stats.max, stat_max],
            ignore_index=True,
        )

    if all(isinstance(file, (str, os.PathLike)) for file in list_files):
        all_files = [str(file) for file in list_files]

        if isinstance(input_file_df, list):
            all_family = ["NaN"] * len(list_files)
        else:
            all_family = input_file_df["Family"].tolist()

    else:
        Console.print("list_files must be a list or a DataFrame")


    all_stats.filename = all_files
    all_stats.family = all_family

    return all_stats
