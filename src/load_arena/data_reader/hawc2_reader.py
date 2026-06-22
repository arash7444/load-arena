# import wetb
import pkgutil
import inspect
import pandas as pd
import pathlib as path

from load_arena.data_reader import LoadArenaConfig

# from load_arena.data_reader import FLEXOutFile
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader.Hawc2io import toDataFrame


def hawc2_reader(sims_path: str | list[str]):
    # out = FLEXOutFile(sims_path)
    # df = out._toDataFrame()
    # print(df.head())

    res_file = ReadHawc2(sims_path)
    info = {}
    data = res_file.ReadAll()
    info["attribute_names"] = res_file.ChInfo[0]
    info["attribute_units"] = res_file.ChInfo[1]
    info["attribute_descr"] = res_file.ChInfo[2]
    df_2 = toDataFrame(data, info)
    print(df_2.head())

    return df_2


if __name__ == "__main__":
    config = LoadArenaConfig(
        sims_path=path.Path(
            r"e:\Projects\Git_Arash\load-arena\tests\h2_res\dlc13\\dlc13_wsp04_wdir000_s023004.int"
        )
    )
    print(config.sims_path)

    df_h2 = hawc2_reader(config.sims_path)
