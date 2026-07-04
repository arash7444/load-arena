import pandas as pd
import pytest

from load_arena.case_loader.input_reader import validate_input_columns
from load_arena.process.concatenate_stats import All_stats
from load_arena.process.family_avg import calc_family_avg


def test_validate_input_columns_suggests_correct_name():
    df_input = pd.DataFrame(
        {
            "folder": ["tests/h2_res/dlc12/"],
            "Timeseries": ["case_001"],
            "Family": [1],
            "PLF": [1.0],
            "Averaging_method": ["mean"],
        }
    )

    with pytest.raises(ValueError, match="'folder' should be 'Folder'"):
        validate_input_columns(df_input)


def test_calc_family_avg_requires_one_method_per_family():
    df_input = pd.DataFrame(
        {
            "Folder": ["tests/h2_res/dlc12/", "tests/h2_res/dlc12/"],
            "Case_folder": ["dlc12", "dlc12"],
            "Timeseries": ["case_001", "case_002"],
            "Family": [1, 1],
            "PLF": [1.0, 1.0],
            "Averaging_method": ["mean", "max"],
        }
    )
    all_stats = _all_stats_for_two_cases()

    with pytest.raises(ValueError, match="Family 1 must have exactly one averaging method"):
        calc_family_avg(all_stats, df_input)


def test_calc_family_avg_rejects_unknown_method():
    df_input = pd.DataFrame(
        {
            "Folder": ["tests/h2_res/dlc12/"],
            "Case_folder": ["dlc12"],
            "Timeseries": ["case_001"],
            "Family": [1],
            "PLF": [1.0],
            "Averaging_method": ["average"],
        }
    )
    all_stats = _all_stats_for_one_case()

    with pytest.raises(ValueError, match="Allowed values are: mean, max, mean_max"):
        calc_family_avg(all_stats, df_input)


def test_calc_family_avg_mean_collects_family_metadata():
    df_input = pd.DataFrame(
        {
            "Folder": ["tests/h2_res/dlc12/", "tests/h2_res/dlc12/"],
            "Case_folder": ["dlc12", "dlc12"],
            "Timeseries": ["case_001", "case_002"],
            "Family": [1, 1],
            "PLF": [1.0, 1.0],
            "Averaging_method": ["mean", "mean"],
        }
    )
    all_stats = _all_stats_for_two_cases()

    family_stats = calc_family_avg(all_stats, df_input)

    assert family_stats.mean["Load"].iloc[0] == 2.0
    assert family_stats.mean.columns[0] == "Family"
    assert family_stats.mean["Family"].iloc[0] == 1
    statistic_tables = [
        family_stats.mean,
        family_stats.std,
        family_stats.min,
        family_stats.max,
        family_stats.mean_plf,
        family_stats.std_plf,
        family_stats.min_plf,
        family_stats.max_plf,
    ]
    assert all(table.columns[0] == "Family" for table in statistic_tables)
    assert all(table["Family"].iloc[0] == 1 for table in statistic_tables)
    assert family_stats.family_name == [1]
    assert family_stats.filename == [["case_001", "case_002"]]


def test_calc_family_avg_supports_grouping_by_family_column():
    """Verify that family-level statistic dataframes can be grouped by Family.

    Parameters
    ----------
    None
        This pytest test creates its input data internally.

    Returns
    -------
    None
        The test passes when the Family column supports grouped access.

    Examples
    --------
    >>> test_calc_family_avg_supports_grouping_by_family_column()
    """
    df_input = pd.DataFrame(
        {
            "Folder": [
                "tests/h2_res/dlc12/",
                "tests/h2_res/dlc12/",
                "tests/h2_res/dlc12/",
            ],
            "Case_folder": ["dlc12", "dlc12", "dlc12"],
            "Timeseries": ["case_001", "case_002", "case_003"],
            "Family": [1, 1, 2],
            "PLF": [1.0, 1.0, 1.0],
            "Averaging_method": ["mean", "mean", "mean"],
        }
    )
    all_stats = All_stats(
        mean=pd.DataFrame({"Load": [1.0, 3.0, 10.0]}),
        std=pd.DataFrame({"Load": [0.1, 0.3, 1.0]}),
        min=pd.DataFrame({"Load": [0.5, 2.5, 9.5]}),
        max=pd.DataFrame({"Load": [1.5, 3.5, 10.5]}),
        mean_plf=pd.DataFrame({"Load": [1.0, 3.0, 10.0]}),
        std_plf=pd.DataFrame({"Load": [0.1, 0.3, 1.0]}),
        min_plf=pd.DataFrame({"Load": [0.5, 2.5, 9.5]}),
        max_plf=pd.DataFrame({"Load": [1.5, 3.5, 10.5]}),
        filename=["case_001", "case_002", "case_003"],
        family=[1, 1, 2],
    )

    family_stats = calc_family_avg(all_stats, df_input)

    grouped_load = family_stats.mean.groupby("Family")["Load"].first().to_dict()
    assert grouped_load == {1: 2.0, 2: 10.0}
    assert family_stats.mean["Load"].tolist() == [2.0, 10.0]
    assert family_stats.family_name == [1, 2]


def _all_stats_for_one_case():
    return All_stats(
        mean=pd.DataFrame({"Load": [1.0]}),
        std=pd.DataFrame({"Load": [0.1]}),
        min=pd.DataFrame({"Load": [0.5]}),
        max=pd.DataFrame({"Load": [1.5]}),
        mean_plf=pd.DataFrame({"Load": [1.0]}),
        std_plf=pd.DataFrame({"Load": [0.1]}),
        min_plf=pd.DataFrame({"Load": [0.5]}),
        max_plf=pd.DataFrame({"Load": [1.5]}),
        filename=["case_001"],
        family=[1],
    )


def _all_stats_for_two_cases():
    return All_stats(
        mean=pd.DataFrame({"Load": [1.0, 3.0]}),
        std=pd.DataFrame({"Load": [0.1, 0.3]}),
        min=pd.DataFrame({"Load": [0.5, 2.5]}),
        max=pd.DataFrame({"Load": [1.5, 3.5]}),
        mean_plf=pd.DataFrame({"Load": [1.0, 3.0]}),
        std_plf=pd.DataFrame({"Load": [0.1, 0.3]}),
        min_plf=pd.DataFrame({"Load": [0.5, 2.5]}),
        max_plf=pd.DataFrame({"Load": [1.5, 3.5]}),
        filename=["case_001", "case_002"],
        family=[1, 1],
    )
