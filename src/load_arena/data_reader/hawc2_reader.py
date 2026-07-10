from PIL import GimpGradientFile
from logging import config
import pathlib as path
import pandas as pd
from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader.Hawc2io import toDataFrame




def read_hawc2_flex(filen_name=None) -> pd.DataFrame:
    """
    Read a single HAWc2 result file.

    Parameters
    ----------
    filen_name : str, optional
        The path to the result file.
        If None, the default path will be used.

    Returns
    -------

    df : pd.DataFrame
        A DataFrame containing the simulation results.

    
    Examples
    --------
    >>> test_read_hawc2_flex()
    """
    if filen_name is None:
        # file = path.Path(
        #     r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
        # )
        raise FileNotFoundError("No file name provided")
    else:
        file = filen_name


    config = LoadArenaConfig(sims_path=file)
    res_file = ReadHawc2(config.sims_path)
    data = res_file.ReadAll()

    info = res_file.ChInfo
    df_1 = toDataFrame(data, info)

    azimuth = df_1["Azi1_[deg]"].max().round(0)
    assert azimuth == 180, f"Azimuth is {azimuth} and should be 180"
    return df_1


def read_hawc2_sel(file_name: str | Path | None = None) -> pd.DataFrame:

    if file_name is None:
        # file = path.Path(r".\tests\h2_res\sel_res\nrel_5mw_reference_wind_turbine")
        raise FileNotFoundError("No file name provided")
    else:
        file = file_name
        
    config = LoadArenaConfig(
    sims_path=path.Path(
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
    return df_2



if __name__ == "__main__":
    file_flex = path.Path(
    r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
)

    df_flex = read_hawc2_flex(file_flex)
    print(df_flex.head())   

    file_sel = path.Path(
    r".\tests\h2_res\sel_res\nrel_5mw_reference_wind_turbine"
)
    df_sel = read_hawc2_sel(file_sel)
    print(df_sel.head())

