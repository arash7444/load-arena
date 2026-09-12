import pandas as pd
import pytest

from load_arena.process.concatenate_stats import All_stats
from load_arena.process.family_avg import FamilyAvg, calc_family_avg
from load_arena.process.uls import ULSStats, calc_uls


def test_calc_uls_uses_plf_stats_without_inventing_filenames():
    """Verify PLF-based ULS values do not invent legacy source filenames.

    Parameters
    ----------
    None
        The test builds family and per-simulation statistics internally.

    Returns
    -------
    None
        The test passes when ULS values are correct and absent provenance stays
        absent.

    Examples
    --------
    >>> test_calc_uls_uses_plf_stats_without_inventing_filenames()
    """
    family_stats = FamilyAvg(
        mean=pd.DataFrame(),
        std=pd.DataFrame(),
        min=pd.DataFrame({"Family": [1, 2], "Load": [-100.0, -6.0]}),
        max=pd.DataFrame({"Family": [1, 2], "Load": [200.0, 4.0]}),
        mean_plf=pd.DataFrame(),
        std_plf=pd.DataFrame(),
        min_plf=pd.DataFrame(
            {
                "Family": [1, 2],
                "Load": [-10.0, -6.0],
                "Moment": [-2.0, -8.0],
            }
        ),
        max_plf=pd.DataFrame(
            {
                "Family": [1, 2],
                "Load": [7.0, 9.0],
                "Moment": [4.0, 8.0],
            }
        ),
        filename=[["case_001", "case_002"], ["case_003"]],
        family_name=[1, 2],
        case_folder=[["dlc12", "dlc12"], ["dlc13"]],
    )
    all_stats = All_stats(
        mean=pd.DataFrame({"Load": [0.0, 0.0, 0.0], "Moment": [0.0, 0.0, 0.0]}),
        std=pd.DataFrame({"Load": [0.0, 0.0, 0.0], "Moment": [0.0, 0.0, 0.0]}),
        min=pd.DataFrame(
            {"Load": [-100.0, -90.0, -6.0], "Moment": [-2.0, -1.0, -8.0]}
        ),
        max=pd.DataFrame(
            {"Load": [200.0, 150.0, 4.0], "Moment": [2.0, 4.0, 8.0]}
        ),
        mean_plf=pd.DataFrame(
            {"Load": [0.0, 0.0, 0.0], "Moment": [0.0, 0.0, 0.0]}
        ),
        std_plf=pd.DataFrame(
            {"Load": [0.0, 0.0, 0.0], "Moment": [0.0, 0.0, 0.0]}
        ),
        min_plf=pd.DataFrame(
            {"Load": [-10.0, -8.0, -6.0], "Moment": [-2.0, -1.0, -8.0]}
        ),
        max_plf=pd.DataFrame(
            {"Load": [7.0, 5.0, 9.0], "Moment": [2.0, 4.0, 8.0]}
        ),
        filename=["case_001", "case_002", "case_003"],
        family=[1, 1, 2],
    )

    uls_stats = calc_uls(family_stats, all_stats)

    assert uls_stats.family_stats is family_stats
    assert uls_stats.ULS["max_Load"].tolist() == [9.0]
    assert uls_stats.ULS["max_Load_filename"].tolist() == [None]
    assert uls_stats.ULS["min_Load"].tolist() == [-10.0]
    assert uls_stats.ULS["min_Load_filename"].tolist() == [None]
    assert uls_stats.Family_ULS["max_Load"].tolist() == [7.0, 9.0]
    assert uls_stats.Family_ULS["max_Load_filename"].tolist() == [None, None]
    assert uls_stats.Family_ULS["min_Moment"].tolist() == [-2.0, -8.0]
    assert uls_stats.Family_ULS["min_Moment_filename"].tolist() == [None, None]
    assert "Family" not in uls_stats.ULS.columns
    assert uls_stats.ULS["AbsMax_Load"].iloc[0] == -10.0
    assert uls_stats.ULS["AbsMax_Load_filename"].iloc[0] is None
    assert uls_stats.ULS["AbsMax_Moment"].iloc[0] == 8.0
    assert uls_stats.ULS["AbsMax_Moment_filename"].iloc[0] is None

    assert uls_stats.Family_ULS["Family"].tolist() == [1, 2]
    assert uls_stats.Family_ULS["AbsMax_Load"].tolist() == [-10.0, 9.0]
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].tolist() == [None, None]
    assert uls_stats.Family_ULS["AbsMax_Moment"].tolist() == [4.0, 8.0]
    assert uls_stats.Family_ULS["AbsMax_Moment_filename"].tolist() == [None, None]


    # A global absolute tie must prefer the max side even in a later family.
    family_stats.max_plf.loc[1, "Load"] = 10.0
    all_stats.max_plf.loc[2, "Load"] = 10.0
    tied = calc_uls(family_stats, all_stats)
    assert tied.ULS["AbsMax_Load"].iloc[0] == 10.0
    assert tied.ULS["AbsMax_Load_filename"].iloc[0] is None

    # Signed min/max comparisons also work for channels entirely on one side of zero.
    for minima, maxima, expected_min, expected_max, expected_abs in (
        ([-10.0, -6.0], [-7.0, -2.0], -10.0, -2.0, -10.0),
        ([2.0, 4.0], [7.0, 9.0], 2.0, 9.0, 9.0),
    ):
        family_stats.min_plf["Load"] = minima
        family_stats.max_plf["Load"] = maxima
        signed = calc_uls(family_stats, all_stats)
        assert signed.ULS["min_Load"].iloc[0] == expected_min
        assert signed.ULS["max_Load"].iloc[0] == expected_max
        assert signed.ULS["AbsMax_Load"].iloc[0] == expected_abs


def test_calc_uls_does_not_invent_source_for_aggregated_values():
    """Verify aggregated family-level values receive no invented source file.

    Parameters
    ----------
    None
        The test creates aggregated family PLF values that are not exact source
        simulation values.

    Returns
    -------
    None
        The test passes when aggregate filename fields remain empty.

    Examples
    --------
    >>> test_calc_uls_does_not_invent_source_for_aggregated_values()
    """
    family_stats = FamilyAvg(
        mean=pd.DataFrame(),
        std=pd.DataFrame(),
        min=pd.DataFrame(),
        max=pd.DataFrame(),
        mean_plf=pd.DataFrame(),
        std_plf=pd.DataFrame(),
        min_plf=pd.DataFrame({"Family": [1], "Load": [-9.0]}),
        max_plf=pd.DataFrame({"Family": [1], "Load": [3.0]}),
        filename=[["case_001", "case_002"]],
        family_name=[1],
        case_folder=[["dlc12", "dlc12"]],
    )
    all_stats = All_stats(
        mean=pd.DataFrame({"Load": [0.0, 0.0]}),
        std=pd.DataFrame({"Load": [0.0, 0.0]}),
        min=pd.DataFrame({"Load": [-12.0, -6.0]}),
        max=pd.DataFrame({"Load": [2.0, 4.0]}),
        mean_plf=pd.DataFrame({"Load": [0.0, 0.0]}),
        std_plf=pd.DataFrame({"Load": [0.0, 0.0]}),
        min_plf=pd.DataFrame({"Load": [-12.0, -6.0]}),
        max_plf=pd.DataFrame({"Load": [2.0, 4.0]}),
        filename=["case_001", "case_002"],
        family=[1, 1],
    )

    uls_stats = calc_uls(family_stats, all_stats)

    assert uls_stats.Family_ULS["min_Load"].iloc[0] == -9.0
    assert uls_stats.Family_ULS["max_Load"].iloc[0] == 3.0
    assert uls_stats.Family_ULS["max_Load_filename"].iloc[0] is None
    assert uls_stats.Family_ULS["AbsMax_Load"].iloc[0] == -9.0
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].iloc[0] is None


def test_calc_uls_suffixes_manually_duplicated_channel_names():
    """Verify ULS handles manually built stats with duplicate channel labels.

    Parameters
    ----------
    None
        The test creates duplicate ``Load`` columns directly in the statistics
        DataFrames.

    Returns
    -------
    None
        The test passes when ULS values are calculated for each duplicate
        channel without pandas Series truth-value errors.

    Examples
    --------
    >>> test_calc_uls_suffixes_manually_duplicated_channel_names()
    """
    family_stats = FamilyAvg(
        mean=pd.DataFrame(),
        std=pd.DataFrame(),
        min=pd.DataFrame(),
        max=pd.DataFrame(),
        mean_plf=pd.DataFrame(),
        std_plf=pd.DataFrame(),
        min_plf=pd.DataFrame([[1, -10.0, -3.0]], columns=["Family", "Load", "Load"]),
        max_plf=pd.DataFrame([[1, 7.0, 5.0]], columns=["Family", "Load", "Load"]),
        filename=[["case_001", "case_002"]],
        family_name=[1],
        case_folder=[["dlc12", "dlc12"]],
    )
    all_stats = All_stats(
        mean=pd.DataFrame([[0.0, 0.0]], columns=["Load", "Load"]),
        std=pd.DataFrame([[0.0, 0.0]], columns=["Load", "Load"]),
        min=pd.DataFrame([[-10.0, -3.0], [-8.0, -2.0]], columns=["Load", "Load"]),
        max=pd.DataFrame([[7.0, 4.0], [6.0, 5.0]], columns=["Load", "Load"]),
        mean_plf=pd.DataFrame([[0.0, 0.0]], columns=["Load", "Load"]),
        std_plf=pd.DataFrame([[0.0, 0.0]], columns=["Load", "Load"]),
        min_plf=pd.DataFrame(
            [[-10.0, -3.0], [-8.0, -2.0]],
            columns=["Load", "Load"],
        ),
        max_plf=pd.DataFrame(
            [[7.0, 4.0], [6.0, 5.0]],
            columns=["Load", "Load"],
        ),
        filename=["case_001", "case_002"],
        family=[1, 1],
    )

    uls_stats = calc_uls(family_stats, all_stats)

    assert uls_stats.Family_ULS["AbsMax_Load"].iloc[0] == -10.0
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].iloc[0] is None
    assert uls_stats.Family_ULS["AbsMax_Load__2"].iloc[0] == 5.0
    assert uls_stats.Family_ULS["AbsMax_Load__2_filename"].iloc[0] is None
    assert uls_stats.ULS["AbsMax_Load"].iloc[0] == -10.0
    assert uls_stats.ULS["AbsMax_Load__2"].iloc[0] == 5.0


def test_uls_stats_legacy_construction_keeps_family_stats_optional():
    """Preserve direct two-table ULSStats construction for existing callers.

    Parameters
    ----------
    None
        The test constructs its inputs directly.

    Returns
    -------
    None
        The legacy constructor succeeds with an absent family-average result.

    Examples
    --------
    >>> test_uls_stats_legacy_construction_keeps_family_stats_optional()
    """
    result = ULSStats(ULS=pd.DataFrame(), Family_ULS=pd.DataFrame())
    second = ULSStats(ULS=pd.DataFrame(), Family_ULS=pd.DataFrame())
    family_arguments = {
        name: pd.DataFrame()
        for name in (
            "mean", "std", "min", "max", "mean_plf", "std_plf", "min_plf",
            "max_plf",
        )
    }
    first_family = FamilyAvg(
        **family_arguments, filename=[], family_name=[], case_folder=[],
    )
    second_family = FamilyAvg(
        **family_arguments, filename=[], family_name=[], case_folder=[],
    )

    assert result.family_stats is None
    result.global_provenance.loc[0, "channel"] = "Load"
    assert second.global_provenance.empty
    first_family.provenance.loc[0, "channel"] = "Load"
    assert second_family.provenance.empty


def test_three_family_averaging_and_global_uls_regression():
    """Verify the complete three-family calculation and provenance chain.

    Parameters
    ----------
    None
        The test builds the approved three-family regression dataset internally.

    Returns
    -------
    None
        The test passes when family values, contributors, and global ULS agree.

    Examples
    --------
    >>> test_three_family_averaging_and_global_uls_regression()
    """
    family_maxima = {
        1: [170216.00, 207685.76, 166127.00, 178000.00],
        2: [154927.00, 170000.00, 160000.00, 150000.00],
        3: [170216.00, 207685.76, 178000.00, 190000.00],
    }
    family_minima = {
        1: [-10.0, -20.0, -30.0, -40.0],
        2: [-11.0, -50.0, -20.0, -30.0],
        3: [-10.0, -40.0, -30.0, -20.0],
    }
    methods = {1: "mean", 2: "max", 3: "mean_half"}
    families = [family for family in family_maxima for _ in range(4)]
    maxima = [value for family in family_maxima.values() for value in family]
    minima = [value for family in family_minima.values() for value in family]
    source_paths = [
        rf"D:\campaign\family_{family}\case_{case}.int"
        for family in family_maxima
        for case in range(1, 5)
    ]
    zeros = pd.DataFrame({"TowerMx_[kNm]": [0.0] * len(families)})
    raw_min = pd.DataFrame({"TowerMx_[kNm]": minima})
    raw_max = pd.DataFrame({"TowerMx_[kNm]": maxima})
    all_stats = All_stats(
        mean=zeros.copy(),
        std=zeros.copy(),
        min=raw_min.copy(),
        max=raw_max.copy(),
        mean_plf=zeros.copy(),
        std_plf=zeros.copy(),
        min_plf=raw_min.copy(),
        max_plf=raw_max.copy(),
        filename=source_paths,
        family=families,
    )
    df_input = pd.DataFrame(
        {
            "Folder": [rf"D:\campaign\family_{family}" for family in families],
            "Case_folder": [f"family_{family}" for family in families],
            "Timeseries": [f"case_{case}.int" for _ in range(3) for case in range(1, 5)],
            "Family": families,
            "PLF": [1.0] * len(families),
            "Averaging_method": [methods[family] for family in families],
        }
    )

    family_stats = calc_family_avg(all_stats, df_input)

    assert all_stats.max["TowerMx_[kNm]"].tolist() == maxima
    assert family_stats.family_name == [1, 2, 3]
    assert family_stats.filename[0] == [
        "case_1.int", "case_2.int", "case_3.int", "case_4.int"
    ]
    assert family_stats.case_folder == [
        ["family_1"] * 4, ["family_2"] * 4, ["family_3"] * 4
    ]
    assert family_stats.max["TowerMx_[kNm]"].tolist() == pytest.approx(
        [180507.19, 170000.00, 198842.88]
    )
    assert family_stats.max_plf["TowerMx_[kNm]"].tolist() == pytest.approx(
        [180507.19, 170000.00, 198842.88]
    )
    assert family_stats.min["TowerMx_[kNm]"].tolist() == pytest.approx(
        [-25.0, -50.0, -35.0]
    )
    assert family_stats.min_plf["TowerMx_[kNm]"].tolist() == pytest.approx(
        [-25.0, -50.0, -35.0]
    )

    raw_max_provenance = family_stats.provenance.loc[
        (family_stats.provenance["statistic"] == "max")
        & ~family_stats.provenance["plf_adjusted"]
    ].reset_index(drop=True)
    assert raw_max_provenance.loc[0, "averaging_method"] == "mean"
    assert raw_max_provenance.loc[0, "member_files"] == tuple(source_paths[:4])
    assert raw_max_provenance.loc[0, "contributing_files"] == tuple(source_paths[:4])
    assert raw_max_provenance.loc[0, "source_file"] is None
    assert raw_max_provenance.loc[1, "contributing_files"] == (source_paths[5],)
    assert raw_max_provenance.loc[1, "source_file"] == source_paths[5]
    assert raw_max_provenance.loc[2, "averaging_method"] == "mean_half"
    assert raw_max_provenance.loc[2, "contributing_files"] == (
        source_paths[9], source_paths[11]
    )
    assert raw_max_provenance.loc[2, "source_file"] is None

    all_stats.min_plf["TowerMx_[kNm]"] = 999999.0
    all_stats.max_plf["TowerMx_[kNm]"] = -999999.0
    uls_stats = calc_uls(family_stats, all_stats)

    assert uls_stats.Family_ULS["max_TowerMx_[kNm]"].tolist() == pytest.approx(
        [180507.19, 170000.00, 198842.88]
    )
    assert uls_stats.ULS["max_TowerMx_[kNm]"].iloc[0] == pytest.approx(198842.88)
    assert uls_stats.Family_ULS["max_TowerMx_[kNm]_filename"].tolist() == [
        None, source_paths[5], None
    ]
    assert uls_stats.ULS["max_TowerMx_[kNm]_filename"].iloc[0] is None

    global_max = uls_stats.global_provenance.loc[
        (uls_stats.global_provenance["channel"] == "TowerMx_[kNm]")
        & (uls_stats.global_provenance["side"] == "max")
    ].iloc[0]
    assert global_max["Family"] == 3
    assert global_max["averaging_method"] == "mean_half"
    assert global_max["member_count"] == 4
    assert global_max["contributing_files"] == (source_paths[9], source_paths[11])
    assert global_max["source_file"] is None
