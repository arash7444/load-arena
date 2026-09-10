import pandas as pd

from load_arena.process.concatenate_stats import All_stats
from load_arena.process.family_avg import FamilyAvg
from load_arena.process.uls import calc_uls


def test_calc_uls_uses_plf_stats_and_tracks_filenames():
    """Verify PLF-based ULS values and source filenames.

    Parameters
    ----------
    None
        The test builds family and per-simulation statistics internally.

    Returns
    -------
    None
        The test passes when ULS values and filename provenance are correct.

    Examples
    --------
    >>> test_calc_uls_uses_plf_stats_and_tracks_filenames()
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

    assert uls_stats.ULS["max_Load"].tolist() == [9.0]
    assert uls_stats.ULS["max_Load_filename"].tolist() == ["case_003"]
    assert uls_stats.ULS["min_Load"].tolist() == [-10.0]
    assert uls_stats.ULS["min_Load_filename"].tolist() == ["case_001"]
    assert uls_stats.Family_ULS["max_Load"].tolist() == [7.0, 9.0]
    assert uls_stats.Family_ULS["max_Load_filename"].tolist() == ["case_001", "case_003"]
    assert uls_stats.Family_ULS["min_Moment"].tolist() == [-2.0, -8.0]
    assert uls_stats.Family_ULS["min_Moment_filename"].tolist() == ["case_001", "case_003"]
    assert "Family" not in uls_stats.ULS.columns
    assert uls_stats.ULS["AbsMax_Load"].iloc[0] == -10.0
    assert uls_stats.ULS["AbsMax_Load_filename"].iloc[0] == "case_001"
    assert uls_stats.ULS["AbsMax_Moment"].iloc[0] == 8.0
    assert uls_stats.ULS["AbsMax_Moment_filename"].iloc[0] == "case_003"

    assert uls_stats.Family_ULS["Family"].tolist() == [1, 2]
    assert uls_stats.Family_ULS["AbsMax_Load"].tolist() == [-10.0, 9.0]
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].tolist() == ["case_001", "case_003"]
    assert uls_stats.Family_ULS["AbsMax_Moment"].tolist() == [4.0, 8.0]
    assert uls_stats.Family_ULS["AbsMax_Moment_filename"].tolist() == [
        "case_002",
        "case_003",
    ]


    # A global absolute tie must prefer the max side even in a later family.
    family_stats.max_plf.loc[1, "Load"] = 10.0
    all_stats.max_plf.loc[2, "Load"] = 10.0
    tied = calc_uls(family_stats, all_stats)
    assert tied.ULS["AbsMax_Load"].iloc[0] == 10.0
    assert tied.ULS["AbsMax_Load_filename"].iloc[0] == "case_003"

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


def test_calc_uls_traces_closest_source_when_family_value_is_aggregated():
    """Verify filename tracing for aggregated family-level values.

    Parameters
    ----------
    None
        The test creates aggregated family PLF values that are not exact source
        simulation values.

    Returns
    -------
    None
        The test passes when the closest source value on the selected side is
        used for filename provenance.

    Examples
    --------
    >>> test_calc_uls_traces_closest_source_when_family_value_is_aggregated()
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
    assert uls_stats.Family_ULS["max_Load_filename"].iloc[0] == "case_001"
    assert uls_stats.Family_ULS["AbsMax_Load"].iloc[0] == -9.0
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].iloc[0] == "case_001"


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
    assert uls_stats.Family_ULS["AbsMax_Load_filename"].iloc[0] == "case_001"
    assert uls_stats.Family_ULS["AbsMax_Load__2"].iloc[0] == 5.0
    assert uls_stats.Family_ULS["AbsMax_Load__2_filename"].iloc[0] == "case_002"
    assert uls_stats.ULS["AbsMax_Load"].iloc[0] == -10.0
    assert uls_stats.ULS["AbsMax_Load__2"].iloc[0] == 5.0
