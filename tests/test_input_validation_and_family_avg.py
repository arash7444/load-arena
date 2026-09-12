import pandas as pd
import pytest

from load_arena.case_loader.input_reader import (
    read_fls_input_file,
    read_input_file,
    validate_input_columns,
)
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


def test_validate_input_columns_rejects_missing_schema_discriminator():
    """Verify schema inference rejects input with no ULS or FLS discriminator.

    Parameters
    ----------
    None
        This test creates its input table internally.

    Returns
    -------
    None
        The test passes when schema inference raises a clear ``ValueError``.

    Examples
    --------
    >>> test_validate_input_columns_rejects_missing_schema_discriminator()
    """
    df_input = pd.DataFrame(
        {
            "Folder": ["tests/h2_res/dlc12/"],
            "Case_folder": ["dlc12"],
            "Timeseries": ["case_001"],
        }
    )

    with pytest.raises(ValueError, match="Cannot determine input type"):
        validate_input_columns(df_input)


def test_validate_input_columns_rejects_ambiguous_schema():
    """Verify schema inference rejects tables containing both discriminators.

    Parameters
    ----------
    None
        This test creates its input table internally.

    Returns
    -------
    None
        The test passes when ambiguous inference raises ``ValueError``.

    Examples
    --------
    >>> test_validate_input_columns_rejects_ambiguous_schema()
    """
    df_input = pd.DataFrame(
        {
            "Family": [1],
            "Occurrences": [10],
        }
    )

    with pytest.raises(ValueError, match="Cannot determine input type"):
        validate_input_columns(df_input)


def test_read_fls_input_file_uses_explicit_schema():
    """Verify the FLS reader validates and returns the checked-in FLS input.

    Parameters
    ----------
    None
        This test reads the checked-in CSV fixture.

    Returns
    -------
    None
        The test passes when the FLS schema is accepted.

    Examples
    --------
    >>> test_read_fls_input_file_uses_explicit_schema()
    """
    df_input = read_fls_input_file("tests/input_file/FLS_input_file.csv")

    assert "Occurrences" in df_input.columns
    assert "Family" not in df_input.columns


def test_read_input_file_warns_and_preserves_uls_compatibility():
    """Verify the deprecated input reader still returns validated ULS data.

    Parameters
    ----------
    None
        This test reads the checked-in CSV fixture.

    Returns
    -------
    None
        The test passes when the alias warns and returns the ULS table.

    Examples
    --------
    >>> test_read_input_file_warns_and_preserves_uls_compatibility()
    """
    with pytest.warns(DeprecationWarning, match="read_uls_input_file"):
        df_input = read_input_file("tests/input_file/ULS_input_file.csv")

    assert "Family" in df_input.columns
    assert "Occurrences" not in df_input.columns


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


@pytest.mark.parametrize("method", ["average", "mean_max"])
def test_calc_family_avg_rejects_unknown_method(method):
    """Reject unsupported averaging methods, including the removed old name.

    Parameters
    ----------
    method : str
        Unsupported family averaging method.

    Returns
    -------
    None
        The test passes when validation lists only the current method names.

    Examples
    --------
    >>> # Run: pytest tests/test_input_validation_and_family_avg.py -k unknown
    """
    df_input = pd.DataFrame(
        {
            "Folder": ["tests/h2_res/dlc12/"],
            "Case_folder": ["dlc12"],
            "Timeseries": ["case_001"],
            "Family": [1],
            "PLF": [1.0],
            "Averaging_method": [method],
        }
    )
    all_stats = _all_stats_for_one_case()

    with pytest.raises(ValueError, match="Allowed values are: mean, max, mean_half"):
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

    # Four signed samples distinguish the lowest half from the highest half.
    df_input = pd.concat([df_input, df_input], ignore_index=True)
    all_stats.family = [1] * 4
    all_stats.filename = ["a", "b", "c", "d"]
    for statistic in ("mean", "std", "min", "max", "mean_plf", "std_plf", "min_plf", "max_plf"):
        values = [-12.0, -8.0, -4.0, -2.0] if statistic.startswith("min") else [1.0, 3.0, 5.0, 9.0]
        setattr(all_stats, statistic, pd.DataFrame({"Load": values}))
    for method, expected_min, expected_max in (("mean", -6.5, 4.5), ("max", -12.0, 9.0), ("mean_half", -10.0, 7.0)):
        df_input["Averaging_method"] = method
        aggregated = calc_family_avg(all_stats, df_input)
        for suffix in ("", "_plf"):
            assert getattr(aggregated, f"min{suffix}")["Load"].iloc[0] == expected_min
            assert getattr(aggregated, f"max{suffix}")["Load"].iloc[0] == expected_max

    df_input["Averaging_method"] = "max"
    all_stats.max = pd.DataFrame({"Load": [9.0, 9.0, 5.0, 1.0]})
    all_stats.max_plf = all_stats.max.copy()
    tied = calc_family_avg(all_stats, df_input)
    tied_max = tied.provenance.loc[
        (tied.provenance["statistic"] == "max")
        & ~tied.provenance["plf_adjusted"]
    ].iloc[0]
    assert tied_max["contributing_files"] == ("a", "b")
    assert tied_max["source_file"] is None

    assert set(family_stats.provenance["averaging_method"]) == {"mean"}
    assert family_stats.provenance["member_count"].eq(2).all()
    assert family_stats.provenance.iloc[0]["member_files"] == ("case_001", "case_002")



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
