from scipy.spatial import cKDTree
from pandas.core.array_algos import masked_accumulations
from pandas import Timedelta
from dataclasses import dataclass
import pandas as pd
from rich.console import Console
from typing import List, Dict
console = Console()

from load_arena.process.concatenate_stats import concatenate_stats
from load_arena.case_loader import read_input_file

from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files



@dataclass
class FamilyAvg:
    family_name: str
    mean: pd.DataFrame
    std: pd.DataFrame
    min: pd.DataFrame
    max: pd.DataFrame
    filename: List[str]
    family_name: List[str]
    

def calc_family_avg(all_stats: pd.DataFrame, df_input: pd.DataFrame) -> pd.DataFrame:

    """
    based on Family number from input file -> compute average values of the relvant time-series

    Parameters
    ----------
    df_stats : pd.DataFrame
        Dataframe containing all stats from concatenating individual statistics

    df_input : pd.DataFrame
        Dataframe containing input information from input file (CSV file)

    Returns
    -------
    family_avg : pd.DataFrame
        Dataframe containing average values of the relvant time-series

    Examples
    --------
    >>> file_name = r".\tests\input_file\input_file.csv"
    >>> df_input = read_input_file(file_name)
    >>> all_stats_hawc2 = concatenate_stats(input_file_df=df_input)
    >>> family_stats = calc_family_avg(all_stats_hawc2, df_input)
    >>> console.print("mean: \n",family_stats.mean)
    >>> console.print("std: \n",family_stats.std)
    >>> console.print("min: \n",family_stats.min)
    >>> console.print("max: \n",family_stats.max)
    >>> console.print("filename: \n",family_stats.filename)
    >>> console.print("family_name: \n",family_stats.family_name)

    """
    family_stats = FamilyAvg(
        mean=pd.DataFrame(),
        std=pd.DataFrame(),
        min=pd.DataFrame(),
        max=pd.DataFrame(),
        filename=[],
        family_name=[],
    )

    family_uniq = pd.unique(df_input["Family"])
    console.print('list of unique families:', family_uniq)

    for family in family_uniq:
        console.print("Processing family:", family)
        ## Create a boolean mask from the family list
        mask = pd.Series(all_stats.family) == family
        mask_input = df_input[df_input["Family"] == family]["Averaging_method"].values.unique()
        mask_filename = df_input[df_input["Family"] == family]["Timeseries"].values.tolist()

        ## from that bolean mask, filter the individual DataFrames inside the dataclass
        mask_mean = all_stats.mean[mask.values]
        mask_std = all_stats.std[mask.values]
        mask_min = all_stats.min[mask.values]
        mask_max = all_stats.max[mask.values]


        ## based on averaging method from input file compute average values
        if mask_input == "mean":
            fam_mean = mask_mean.mean(axis=0).to_frame().T # average values of each column
            fam_std = mask_std.mean(axis=0).to_frame().T
            fam_min = mask_min.mean(axis=0).to_frame().T
            fam_max = mask_max.mean(axis=0).to_frame().T
        elif mask_input == "max":
            fam_mean = mask_mean.max(axis=0).to_frame().T # max values of each column
            fam_std = mask_std.max(axis=0).to_frame().T
            fam_min = mask_min.max(axis=0).to_frame().T
            fam_max = mask_max.max(axis=0).to_frame().T
        elif mask_input == "mean_max":
            sorted_mean = mask_mean.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_std = mask_std.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_min = mask_min.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_max = mask_max.apply(lambda x: x.sort_values(ascending=False).values)

            half_len = int(len(mask_mean)/2) # 1/2 of each input time series
            
            fam_mean = sorted_mean.iloc[:half_len,:].mean().to_frame().T # Take the mean of the top half (rows)
            fam_std = sorted_std.iloc[:half_len,:].mean().to_frame().T
            fam_min = sorted_min.iloc[:half_len,:].mean().to_frame().T
            fam_max = sorted_max.iloc[:half_len,:].mean().to_frame().T


        family_stats.mean = pd.concat(
            [family_stats.mean, fam_mean],
            ignore_index=True,
        )

        family_stats.std = pd.concat(
            [family_stats.std, fam_std],
            ignore_index=True,
        )

        family_stats.min = pd.concat(
            [family_stats.min, fam_min],
            ignore_index=True,
        )

        family_stats.max = pd.concat(
            [family_stats.max, fam_max],
            ignore_index=True,
        )

        family_stats.family_name = family # save family number
        family_stats.filename = mask_filename[0] # keep the first filename of the family



    return family_stats







# if __name__== "__main__":

#     file_name = r".\tests\input_file\input_file.csv"
#     df_input = read_input_file(file_name)
#     list_files = df_input["Folder"] + df_input["Timeseries"]

#     all_stats_hawc2 = concatenate_stats(input_file_df=df_input)

#     family_stats = calc_family_avg(all_stats_hawc2, df_input)


#     console.print("Family average mean: \n",family_stats.mean)
#     console.print("Family average  std: \n",family_stats.std)
#     console.print("Family average min: \n",family_stats.min)
#     console.print("Family average max: \n",family_stats.max)
#     console.print("Family average filename: \n",family_stats.filename)
#     console.print("Family average family_name: \n",family_stats.family_name)