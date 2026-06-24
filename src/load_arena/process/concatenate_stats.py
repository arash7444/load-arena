import pandas as pd
from dataclasses import dataclass
from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats

@dataclass
class All_stats:
    mean: pd.DataFrame
    std: pd.DataFrame
    min: pd.DataFrame
    max: pd.DataFrame
    filename: str

def concatenate_stats(list_files: list) -> All_stats:
    """
    Concatenate a list of All_stats objects into a single DataFrame.

    Parameters:
    -----------
        list_files: list
            A list of file paths corresponding to the statistics.

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
    filename=[]
)
    for file in list_files:
        config = LoadArenaConfig(
            sims_path=file
        )
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
    all_files = [file.name for file in list_files]
    all_stats.filename = all_files

    return all_stats