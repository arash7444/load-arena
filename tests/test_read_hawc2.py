import pandas as pd

from load_arena.data_reader import ReadHawc2
from load_arena.data_reader.Hawc2io import toDataFrame


def test_read_hawc2_flex():
    sims_path = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004.int"
    res_file = ReadHawc2(sims_path)
    data = res_file.ReadAll()
    info = {
        "attribute_names": res_file.ChInfo[0],
        "attribute_units": res_file.ChInfo[1],
        "attribute_descr": res_file.ChInfo[2],
    }
    df_2 = toDataFrame(data, info)

    azimuth = df_2["Azi1_[deg]"].max().round(0)
    assert azimuth == 180, f"Azimuth is {azimuth} and should be 180"


def test_read_hawc2_sel():
    sims_path = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004"
    res_file = ReadHawc2(sims_path)
    results = res_file.ReadAll()
    channelinfo = res_file.ChInfo

    df = pd.DataFrame(results, columns=channelinfo[0])
    azimuth = df["Azi  1"].max().round(0)
    assert azimuth == 180, f"Azimuth is {azimuth} and should be 180"
