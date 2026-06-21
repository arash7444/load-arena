# import wetb
import pkgutil
import inspect
from Hawc2io import ReadHawc2
import pandas as pd
import pathlib as path

from load_arena.data_reader import LoadArenaConfig


def hawc2_reader(sims_path: str | list[str]):

    data = ReadHawc2(sims_path)

    # res_file = data.ReadFLEX()
    res_file = (
        data.ReadAll()
    )  # TODO: check if this is the same as ReadFLEX, and if not, what is the difference

    sensor_data = data.ChInfo[0]

    print(res_file)

    df = pd.DataFrame(res_file, columns=sensor_data)
    # df.insert(0, "Time", data.t) # used when using ReadFLEX, but not needed when using ReadAll, as it already includes the time column

    print(df.head())


if __name__ == "__main__":
    config = LoadArenaConfig(
        sims_path=path.Path(r".h2_res\dlc13\dlc13_wsp11_wdir0_s011001")
    )
    print(config.sims_path)

    df_h2 = hawc2_reader(config.sims_path)
