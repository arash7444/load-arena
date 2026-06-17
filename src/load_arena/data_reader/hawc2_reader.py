# import wetb
import pkgutil
import inspect
from Hawc2io import ReadHawc2
import pandas as pd
import pathlib as Path
import sys
import os


def hawc2_reader(sims_path: str) -> pd.DataFrame:
    file_path = os.path.abspath(sims_path)
    print(file_path)

    file_dir = os.path.dirname(file_path)
    print(f"Reading simulation data from: {file_dir}")

    # sim_dir = os.path.isfile(sims_path)
    # if not sim_dir:
    #     raise ValueError("Invalid simulation path")
    # else:
    #     file_dir = os.path.basename(sims_path)
    #     print(f"Reading simulation data from: {file_dir}")

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
    print(os.getcwd())
    df_h2 = hawc2_reader(sims_path=r".\tests\dlc13\dlc13_wsp11_wdir0_s011001")
