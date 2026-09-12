from scipy.spatial import cKDTree
from pandas.core.array_algos import masked_accumulations
from pandas import Timedelta
from dataclasses import dataclass, field
import pandas as pd
from rich.console import Console
from typing import TYPE_CHECKING, List, Dict, Literal

if TYPE_CHECKING:
    from plotly.graph_objects import Figure
console = Console()

from load_arena.process.concatenate_stats import All_stats, concatenate_stats
from load_arena.case_loader import read_uls_input_file
from load_arena.case_loader.input_reader import validate_case_rows

from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files



@dataclass
class FamilyAvg:
    """Store family-level statistics, metadata, and structured provenance.

    Parameters
    ----------
    mean, std, min, max : pandas.DataFrame
        Stored raw family statistic tables.
    mean_plf, std_plf, min_plf, max_plf : pandas.DataFrame
        Stored PLF-adjusted family statistic tables.
    filename, family_name, case_folder : list
        Compatibility metadata aligned with the family rows.
    provenance : pandas.DataFrame, optional
        Long-form calculation provenance. A new empty table is created for each
        legacy construction that omits this argument.

    Returns
    -------
    FamilyAvg
        Family result container that can be explored without recalculation.

    Examples
    --------
    >>> family_stats = calc_family_avg(all_stats, df_input)
    >>> family_stats.provenance.columns.tolist()
    ['Family', 'statistic', 'plf_adjusted', 'channel', 'channel_position',
     'value', 'averaging_method', 'member_count', 'member_files',
     'contributing_files', 'source_file']
    """

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
    provenance: pd.DataFrame = field(default_factory=pd.DataFrame)

    def explore(
        self, *, channel: str, statistic: Literal["mean", "std", "min", "max"],
        x: str = "Family", plf: bool = False, show: bool = True,
    ) -> "Figure":
        """Plot a stored family statistic without recalculating family averages.

        Parameters
        ----------
        channel : str
            Exact y-axis channel name, including units.
        statistic : {"mean", "std", "min", "max"}
            Stored family statistic to explore.
        x : str, default "Family"
            ``Family`` or an exact channel name from the selected table.
        plf : bool, default False
            Select the corresponding PLF-adjusted table when True.
        show : bool, default True
            Display the figure using Plotly's configured renderer.

        Returns
        -------
        plotly.graph_objects.Figure
            Interactive marker plot of the stored family result.

        Examples
        --------
        >>> fig = family_stats.explore(
        ...     channel="TowerMx_[kNm]", statistic="max", show=False
        ... )
        """
        from load_arena.visualization.family_avg_plots import plot_family_avg

        figure = plot_family_avg(
            self, channel=channel, statistic=statistic, x=x, plf=plf,
        )
        if show:
            figure.show()
        return figure


def _aggregate_family_table(
    table: pd.DataFrame,
    *,
    family: object,
    statistic: Literal["mean", "std", "min", "max"],
    plf_adjusted: bool,
    averaging_method: Literal["mean", "max", "mean_half"],
    member_files: tuple[str, ...],
) -> tuple[pd.DataFrame, list[dict]]:
    """Aggregate one family table and record the contributing simulations.

    Parameters
    ----------
    table : pandas.DataFrame
        Per-simulation values for one family, statistic, and PLF mode.
    family : object
        Family identifier stored with the result and provenance.
    statistic : {"mean", "std", "min", "max"}
        Statistic whose minimum-side ordering determines lower-half selection.
    plf_adjusted : bool
        Whether the supplied values include partial load factors.
    averaging_method : {"mean", "max", "mean_half"}
        Family aggregation method.
    member_files : tuple[str, ...]
        Full source paths aligned positionally with the table rows.

    Returns
    -------
    tuple[pandas.DataFrame, list[dict]]
        One processed family row and long-form provenance records per channel.

    Examples
    --------
    >>> row, provenance = _aggregate_family_table(
    ...     pd.DataFrame({"Load": [1.0, 3.0]}), family=1, statistic="max",
    ...     plf_adjusted=False, averaging_method="mean_half",
    ...     member_files=("one.int", "two.int"),
    ... )
    >>> row["Load"].iloc[0]
    3.0
    """
    if len(table) != len(member_files):
        raise ValueError("Family table rows must align with member source files.")

    values_by_channel = []
    provenance = []
    for channel_position, channel in enumerate(table.columns):
        values = table.iloc[:, channel_position]
        if averaging_method == "mean":
            value = values.mean()
            contributor_positions = list(range(len(values)))
        elif averaging_method == "max":
            value = values.min() if statistic == "min" else values.max()
            contributor_positions = [
                position for position, candidate in enumerate(values.tolist())
                if candidate == value
            ]
        else:
            ascending = statistic == "min"
            ordered = pd.DataFrame(
                {"value": values.tolist(), "position": range(len(values))}
            ).sort_values("value", ascending=ascending, kind="stable")
            contributor_positions = ordered["position"].iloc[:len(values) // 2].tolist()
            value = values.iloc[contributor_positions].mean()

        contributing_files = tuple(member_files[position] for position in contributor_positions)
        source_file = (
            contributing_files[0]
            if averaging_method == "max" and len(contributing_files) == 1
            else None
        )
        values_by_channel.append(value)
        provenance.append(
            {
                "Family": family,
                "statistic": statistic,
                "plf_adjusted": plf_adjusted,
                "channel": channel,
                "channel_position": channel_position,
                "value": value,
                "averaging_method": averaging_method,
                "member_count": len(member_files),
                "member_files": member_files,
                "contributing_files": contributing_files,
                "source_file": source_file,
            }
        )

    result = pd.DataFrame(
        [[family, *values_by_channel]], columns=["Family", *table.columns]
    )
    return result, provenance


def calc_family_avg(all_stats: All_stats, df_input: pd.DataFrame) -> FamilyAvg:

    """
    Compute family-level statistics from concatenated time-series statistics.

    The ``max`` method selects minima with min and maxima with max.
    ``mean_half`` averages the smallest half of minima and largest half of
    maxima; ``mean`` averages all values. Both raw and PLF tables follow
    these rules.

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
        column, compatibility metadata remains available as lists, and full-path
        contributor provenance is stored in a long-form DataFrame.

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
        provenance=pd.DataFrame(),
    )

    validate_case_rows(df_input, mode="uls")
    family_uniq = pd.unique(df_input["Family"])
    console.print('list of unique families:', family_uniq)
    provenance_records = []

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
        if method not in {"mean", "max", "mean_half"}:
            raise ValueError(
                f"Unknown Averaging_method for family {family}: {method}. "
                "Allowed values are: mean, max, mean_half. "
                "Please fix the input file and run it again."
            )
        mask_filename = df_input[df_input["Family"] == family]["Timeseries"].tolist()
        mask_case_folder = df_input[df_input["Family"] == family]["Case_folder"].tolist()

        if len(all_stats.filename) != len(all_stats.family):
            raise ValueError("all_stats.filename must align with all_stats.family.")
        member_files = tuple(
            str(all_stats.filename[position])
            for position, selected in enumerate(mask.tolist())
            if selected
        )


        ## from that bolean mask, filter the individual DataFrames inside the dataclass
        mask_mean = all_stats.mean[mask.values]
        mask_std = all_stats.std[mask.values]
        mask_min = all_stats.min[mask.values]
        mask_max = all_stats.max[mask.values]

        mask_mean_plf = all_stats.mean_plf[mask.values]
        mask_std_plf = all_stats.std_plf[mask.values]
        mask_min_plf = all_stats.min_plf[mask.values]
        mask_max_plf = all_stats.max_plf[mask.values]


        tables = {
            ("mean", False): mask_mean,
            ("std", False): mask_std,
            ("min", False): mask_min,
            ("max", False): mask_max,
            ("mean", True): mask_mean_plf,
            ("std", True): mask_std_plf,
            ("min", True): mask_min_plf,
            ("max", True): mask_max_plf,
        }
        aggregated = {}
        family_provenance = []
        for (statistic, plf_adjusted), table in tables.items():
            result, records = _aggregate_family_table(
                table,
                family=family,
                statistic=statistic,
                plf_adjusted=plf_adjusted,
                averaging_method=method,
                member_files=member_files,
            )
            aggregated[(statistic, plf_adjusted)] = result
            family_provenance.extend(records)

        fam_mean = aggregated[("mean", False)]
        fam_std = aggregated[("std", False)]
        fam_min = aggregated[("min", False)]
        fam_max = aggregated[("max", False)]
        fam_mean_plf = aggregated[("mean", True)]
        fam_std_plf = aggregated[("std", True)]
        fam_min_plf = aggregated[("min", True)]
        fam_max_plf = aggregated[("max", True)]

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
        provenance_records.extend(family_provenance)

    family_stats.provenance = pd.DataFrame(provenance_records)
    if "source_file" in family_stats.provenance:
        source_files = family_stats.provenance["source_file"].astype(object)
        family_stats.provenance["source_file"] = source_files.where(
            source_files.notna(), None,
        )
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
