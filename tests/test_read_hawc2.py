import pandas as pd

from load_arena.data_reader import ReadHawc2
from load_arena.data_reader.Hawc2io import toDataFrame
from load_arena.data_reader.load_arena_config import LoadArenaConfig
from pathlib import Path

def test_read_hawc2_flex():
    """Verify FLEX-format HAWC2 files are converted to expected columns.

    Parameters
    ----------
    None
        The test reads a checked-in HAWC2 FLEX result fixture.

    Returns
    -------
    None
        The test passes when the azimuth channel has the expected maximum.

    Examples
    --------
    >>> test_read_hawc2_flex()
    """

    config = LoadArenaConfig(
        sims_path=Path(
            r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
        )
    )
    res_file = ReadHawc2(config.sims_path)
    data = res_file.ReadAll()

    info = res_file.ChInfo
    df_1 = toDataFrame(data, info)

    azimuth = df_1["Azi1_[deg]"].max().round(0)
    assert azimuth == 180, f"Azimuth is {azimuth} and should be 180"


def test_read_hawc2_sel():
    """Verify SEL-format HAWC2 files are converted to expected columns.

    Parameters
    ----------
    None
        The test reads a checked-in HAWC2 SEL result fixture.

    Returns
    -------
    None
        The test passes when the azimuth channel has the expected maximum.

    Examples
    --------
    >>> test_read_hawc2_sel()
    """
    
    config = LoadArenaConfig(
    sims_path=Path(
        r".\tests\h2_res\sel_res\nrel_5mw_reference_wind_turbine"
    )
)

    res_file_2 = ReadHawc2(config.sims_path)

    results = res_file_2.ReadAll()
    channelinfo = res_file_2.ChInfo
    df_2 = toDataFrame(results, channelinfo)

    # df = pd.DataFrame(results, columns=channelinfo[0])
    azimuth = df_2["bea1angle_[deg]"].max().round(0)
    assert azimuth == 360, f"Azimuth is {azimuth} and should be 360"


def test_to_dataframe_suffixes_duplicate_final_channel_names():
    """Verify duplicate final channel names receive stable suffixes.

    Parameters
    ----------
    None
        The test creates channel metadata with repeated names and units.

    Returns
    -------
    None
        The test passes when duplicate final labels are suffixed.

    Examples
    --------
    >>> test_to_dataframe_suffixes_duplicate_final_channel_names()
    """
    data = pd.DataFrame([[1.0, 2.0, 3.0]]).to_numpy()
    info = [["Load", "Load", "Moment"], ["kN", "kN", "kNm"], ["", "", ""]]

    df = toDataFrame(data, info)

    assert df.columns.tolist() == ["Load_[kN]", "Load_[kN]__2", "Moment_[kNm]"]


if __name__ == "__main__":
    test_read_hawc2_flex()
    test_read_hawc2_sel()
