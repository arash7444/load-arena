from scipy.spatial import cKDTree
from pandas.core.array_algos import masked_accumulations
from pandas import Timedelta
from dataclasses import dataclass
import pandas as pd
from rich.console import Console
from typing import List, Dict
console = Console()

from load_arena.process.concatenate_stats import All_stats, concatenate_stats
from load_arena.case_loader import read_uls_input_file
from load_arena.case_loader.input_reader import validate_input_columns

from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files



@dataclass
class FamilyAvg:
    mean: pd.DataFrame
    std: pd.DataFrame
    min: pd.DataFrame
    max: pd.DataFrame
    mean_plf: pd.DataFrame
    std_plf: pd.DataFrame
    min_plf: pd.DataFrame
    max_plf: pd.DataFrame
    filename: List[str]
    family_name: List[str]
    case_folder: List[str]
    

def calc_family_avg(all_stats: All_stats, df_input: pd.DataFrame) -> FamilyAvg:

    """
    Compute family-level statistics from concatenated time-series statistics.

    Parameters
    ----------
    all_stats : All_stats
        Concatenated statistics from all input time-series.
    df_input : pd.DataFrame
        Input configuration with family, PLF, case folder, and averaging method columns.

    Returns
    -------
    FamilyAvg
        Family-level statistics where each statistic dataframe includes a ``Family``
        column and the original family metadata remains available as lists.

    Examples
    --------
    >>> file_name = "tests/input_file/ULS_input_file.csv"
    >>> df_input = read_uls_input_file(file_name)
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
        mean_plf=pd.DataFrame(),
        std_plf=pd.DataFrame(),
        min_plf=pd.DataFrame(),
        max_plf=pd.DataFrame(),
        filename=[],
        family_name=[],
        case_folder=[],
    )

    validate_input_columns(df_input)
    family_uniq = pd.unique(df_input["Family"])
    console.print('list of unique families:', family_uniq)

    for family in family_uniq:
        console.print("Processing family:", family)
        ## Create a boolean mask from the family list
        mask = pd.Series(all_stats.family) == family
        methods = df_input.loc[df_input["Family"] == family, "Averaging_method"].unique()
        if len(methods) != 1:
            raise ValueError(
                f"Family {family} must have exactly one averaging method. "
                "Please fix the input file and run it again."
            )
        method = str(methods[0]).strip().lower()
        if method not in {"mean", "max", "mean_max"}:
            raise ValueError(
                f"Unknown Averaging_method for family {family}: {method}. "
                "Allowed values are: mean, max, mean_max. "
                "Please fix the input file and run it again."
            )
        mask_filename = df_input[df_input["Family"] == family]["Timeseries"].tolist()
        mask_case_folder = df_input[df_input["Family"] == family]["Case_folder"].tolist()


        ## from that bolean mask, filter the individual DataFrames inside the dataclass
        mask_mean = all_stats.mean[mask.values]
        mask_std = all_stats.std[mask.values]
        mask_min = all_stats.min[mask.values]
        mask_max = all_stats.max[mask.values]

        mask_mean_plf = all_stats.mean_plf[mask.values]
        mask_std_plf = all_stats.std_plf[mask.values]
        mask_min_plf = all_stats.min_plf[mask.values]
        mask_max_plf = all_stats.max_plf[mask.values]


        ## based on averaging method from input file compute average values
        if method == "mean":
            fam_mean = mask_mean.mean(axis=0).to_frame().T # average values of each column
            fam_std = mask_std.mean(axis=0).to_frame().T
            fam_min = mask_min.mean(axis=0).to_frame().T
            fam_max = mask_max.mean(axis=0).to_frame().T

            fam_mean_plf = mask_mean_plf.mean(axis=0).to_frame().T
            fam_std_plf = mask_std_plf.mean(axis=0).to_frame().T
            fam_min_plf = mask_min_plf.mean(axis=0).to_frame().T
            fam_max_plf = mask_max_plf.mean(axis=0).to_frame().T

            
        elif method == "max":
            fam_mean = mask_mean.max(axis=0).to_frame().T # max values of each column
            fam_std = mask_std.max(axis=0).to_frame().T
            fam_min = mask_min.max(axis=0).to_frame().T
            fam_max = mask_max.max(axis=0).to_frame().T

            fam_mean_plf = mask_mean_plf.max(axis=0).to_frame().T
            fam_std_plf = mask_std_plf.max(axis=0).to_frame().T
            fam_min_plf = mask_min_plf.max(axis=0).to_frame().T
            fam_max_plf = mask_max_plf.max(axis=0).to_frame().T

            
        elif method == "mean_max":
            sorted_mean = mask_mean.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_std = mask_std.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_min = mask_min.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_max = mask_max.apply(lambda x: x.sort_values(ascending=False).values)

            sorted_mean_plf = mask_mean_plf.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_std_plf = mask_std_plf.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_min_plf = mask_min_plf.apply(lambda x: x.sort_values(ascending=False).values)
            sorted_max_plf = mask_max_plf.apply(lambda x: x.sort_values(ascending=False).values)

            half_len = int(len(mask_mean)/2) # 1/2 of each input time series
            
            fam_mean = sorted_mean.iloc[:half_len,:].mean().to_frame().T # Take the mean of the top half (rows)
            fam_std = sorted_std.iloc[:half_len,:].mean().to_frame().T
            fam_min = sorted_min.iloc[:half_len,:].mean().to_frame().T
            fam_max = sorted_max.iloc[:half_len,:].mean().to_frame().T

            fam_mean_plf = sorted_mean_plf.iloc[:half_len,:].mean().to_frame().T # Take the mean of the top half (rows)
            fam_std_plf = sorted_std_plf.iloc[:half_len,:].mean().to_frame().T
            fam_min_plf = sorted_min_plf.iloc[:half_len,:].mean().to_frame().T
            fam_max_plf = sorted_max_plf.iloc[:half_len,:].mean().to_frame().T

            
        for fam_df in (
            fam_mean,
            fam_std,
            fam_min,
            fam_max,
            fam_mean_plf,
            fam_std_plf,
            fam_min_plf,
            fam_max_plf,
        ):
            fam_df.insert(0, "Family", family)

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

        family_stats.mean_plf = pd.concat(
            [family_stats.mean_plf, fam_mean_plf],
            ignore_index=True,
        )

        family_stats.std_plf = pd.concat(
            [family_stats.std_plf, fam_std_plf],
            ignore_index=True,
        )

        family_stats.min_plf = pd.concat(
            [family_stats.min_plf, fam_min_plf],
            ignore_index=True,
        )

        family_stats.max_plf = pd.concat(
            [family_stats.max_plf, fam_max_plf],
            ignore_index=True,
        )

        family_stats.family_name.append(family) # save family number
        family_stats.filename.append(mask_filename) # keep filenames of the family
        family_stats.case_folder.append(mask_case_folder) # keep case folders of the family



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
