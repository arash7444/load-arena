from pathlib import Path

import pandas as pd

from load_arena.data_reader.Hawc2io import ReadHawc2, toDataFrame
from load_arena.data_reader.load_arena_config import LoadArenaConfig


def read_hawc2_flex(file_name: str | Path | None = None) -> pd.DataFrame:
    """Read one FLEX-format HAWC2 result file into a DataFrame.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path or path prefix of the FLEX result file.

    Returns
    -------
    pandas.DataFrame
        Simulation samples with channel names derived from HAWC2 metadata.

    Examples
    --------
    >>> data = read_hawc2_flex("tests/h2_res/dlc13/example")
    >>> isinstance(data, pd.DataFrame)
    True
    """
    if file_name is None:
        raise FileNotFoundError("No file name provided")

    config = LoadArenaConfig(sims_path=Path(file_name))
    result_file = ReadHawc2(config.sims_path)
    return toDataFrame(result_file.ReadAll(), result_file.ChInfo)


def read_hawc2_sel(file_name: str | Path | None = None) -> pd.DataFrame:
    """Read one SEL/DAT-format HAWC2 result file into a DataFrame.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path or path prefix of the SEL/DAT result file.

    Returns
    -------
    pandas.DataFrame
        Simulation samples with channel names derived from HAWC2 metadata.

    Examples
    --------
    >>> data = read_hawc2_sel("tests/h2_res/sel_res/example")
    >>> isinstance(data, pd.DataFrame)
    True
    """
    if file_name is None:
        raise FileNotFoundError("No file name provided")

    config = LoadArenaConfig(sims_path=Path(file_name))
    result_file = ReadHawc2(config.sims_path)
    return toDataFrame(result_file.ReadAll(), result_file.ChInfo)
