# import wetb
import pkgutil
import inspect
from Hawc2io import ReadHawc2
import pandas as pd
import pathlib as path
from

def hawc2_reader(sims_path: str| ):

    data = ReadHawc2(
        r"d:\Projects\Simulation_results\Hawc2\dlc13\dlc13_wsp11_wdir0_s011001"
    )

    # res_file = data.ReadFLEX()
    res_file = data.ReadAll() # TODO: check if this is the same as ReadFLEX, and if not, what is the difference

    sensor_data = data.ChInfo[0]

    print(res_file)

    df = pd.DataFrame(res_file, columns=sensor_data)
    # df.insert(0, "Time", data.t) # used when using ReadFLEX, but not needed when using ReadAll, as it already includes the time column

    print(df.head())


if __name__ == "__main__":

    df_h2 = hawc2_reader()
