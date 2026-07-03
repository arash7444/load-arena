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
            "Timeseries": ["case_001", "case_002"],
            "Family": [1, 1],
            "PLF": [1.0, 1.0],
            "Averaging_method": ["mean", "mean"],
        }
    )
    all_stats = _all_stats_for_two_cases()

    family_stats = calc_family_avg(all_stats, df_input)

    assert family_stats.mean["Load"].iloc[0] == 2.0
    assert family_stats.family_name == [1]
    assert family_stats.filename == [["case_001", "case_002"]]


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
