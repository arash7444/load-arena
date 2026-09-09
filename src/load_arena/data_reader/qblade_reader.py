from pathlib import Path

import pandas as pd

from load_arena.data_reader.Hawc2io import ReadHawc2, toDataFrame
from load_arena.data_reader.load_arena_config import LoadArenaConfig
from load_arena.utils import find_files

def read_qblade(file_name: str | Path | None = None) -> pd.DataFrame:
    """
    Read a QBlade binary result is similar to read a sel result file from HAWC2.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path or path prefix of the QBlade flex result file.

    Returns
    -------
    pandas.DataFrame
        Simulation samples with channel names derived from QBlade metadata.

    Examples
    --------
    >>> data = read_qblade_flex("tests/Qblade_res/steady_10ms")
    >>> isinstance(data, pd.DataFrame)
    True
    """

    if file_name is None:
        raise FileNotFoundError("No file name provided")

    file_name = Path(file_name)

    if file_name.suffix.lower() == ".sel":
        res_file = ReadHawc2(file_name) # Read flex result into data frame
        data = res_file.ReadAll()  
        info = res_file.ChInfo 
        df = toDataFrame(data, info) # Convert data to pandas Dataframe
    elif file_name.suffix.lower() == ".txt":
        df = pd.read_csv(file_name, sep="\t",header=2) # Read ASCII Qblade result
        df.columns = df.columns.str.replace("~[","_[")
        df.columns = df.columns.str.replace("~","")

    else:
        raise ValueError(f"Unsupported file type: {file_name}") 
        


    return df


if __name__ == "__main__":
    qblade_folder = r".\tests\Qblade_res"
    list_files = find_files(folder_name=qblade_folder, file_extension=".txt")

    data = read_qblade(list_files[0])
    print(data.head())