import pathlib as path

from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader.Hawc2io import toDataFrame


def hawc2_reader(sims_path: str | path.Path):
    res_file = ReadHawc2(sims_path)
    data = res_file.ReadAll()
    info = {
        "attribute_names": res_file.ChInfo[0],
        "attribute_units": res_file.ChInfo[1],
        "attribute_descr": res_file.ChInfo[2],
    }

    return toDataFrame(data, info)


if __name__ == "__main__":
    config = LoadArenaConfig(
        sims_path=path.Path(
            r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004.int"
        )
    )
    print(config.sims_path)

    df_h2 = hawc2_reader(config.sims_path)
    print(df_h2.head())
