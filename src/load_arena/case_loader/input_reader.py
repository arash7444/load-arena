from difflib import get_close_matches
from pathlib import Path
from typing import Literal
import warnings

import pandas as pd


REQUIRED_ULS_INPUT_COLUMNS = [
    "Folder",
    "Case_folder",
    "Timeseries",
    "Family",
    "PLF",
    "Averaging_method",
]

REQUIRED_FLS_INPUT_COLUMNS = [
    "Folder",
    "Case_folder",
    "Timeseries",
    "Occurrences",
]


def validate_input_columns(
    df: pd.DataFrame,
    mode: Literal["uls", "fls"] | None = None,
) -> None:
    """Validate the required columns of a ULS or FLS input table.

    Parameters
    ----------
    df : pandas.DataFrame
        Input configuration table to validate.
    mode : {"uls", "fls"} or None, default None
        Explicit schema. When omitted, infer it from exactly one discriminator
        column: ``Family`` for ULS or ``Occurrences`` for FLS.

    Returns
    -------
    None
        Returns after successful validation; otherwise raises an exception.

    Examples
    --------
    >>> table = pd.DataFrame(columns=REQUIRED_FLS_INPUT_COLUMNS)
    >>> validate_input_columns(table, mode="fls")
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df_input must be a pandas DataFrame.")
    if mode not in {None, "uls", "fls"}:
        raise ValueError("mode must be either 'uls', 'fls', or None.")

    if mode is None:
        has_family = "Family" in df.columns
        has_occurrences = "Occurrences" in df.columns
        if has_family == has_occurrences:
            raise ValueError(
                "Cannot determine input type. Provide mode='uls' or mode='fls', "
                "or include exactly one of 'Family' and 'Occurrences'."
            )
        mode = "uls" if has_family else "fls"

    required_columns = (
        REQUIRED_ULS_INPUT_COLUMNS if mode == "uls" else REQUIRED_FLS_INPUT_COLUMNS
    )
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if not missing_columns:
        return

    suggestions = []
    for column in missing_columns:
        matches = get_close_matches(column, df.columns, n=1, cutoff=0.6)
        if matches:
            suggestions.append(f"'{matches[0]}' should be '{column}'")
        else:
            suggestions.append(f"add '{column}'")

    raise ValueError(
        "Input file has wrong or missing column names. "
        f"Please fix the input file and run it again: {', '.join(suggestions)}"
    )


def read_uls_input_file(file_name: str | Path) -> pd.DataFrame:
    """Read and validate a CSV configuration for ULS processing.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path to the ULS CSV input file.

    Returns
    -------
    pandas.DataFrame
        Validated ULS input configuration.

    Examples
    --------
    >>> table = read_uls_input_file("tests/input_file/ULS_input_file.csv")
    >>> "Family" in table.columns
    True
    """
    df_input = read_input_csv(file_name)
    validate_input_columns(df_input, mode="uls")
    return df_input


def read_fls_input_file(file_name: str | Path) -> pd.DataFrame:
    """Read and validate a CSV configuration for FLS processing.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path to the FLS CSV input file.

    Returns
    -------
    pandas.DataFrame
        Validated FLS input configuration.

    Examples
    --------
    >>> table = read_fls_input_file("tests/input_file/FLS_input_file.csv")
    >>> "Occurrences" in table.columns
    True
    """
    df_input = read_input_csv(file_name)
    validate_input_columns(df_input, mode="fls")
    return df_input


def read_input_file(file_name: str | Path) -> pd.DataFrame:
    """Read a ULS input CSV through the deprecated historical API.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path to the ULS CSV input file.

    Returns
    -------
    pandas.DataFrame
        Validated ULS input configuration.

    Examples
    --------
    >>> table = read_input_file("tests/input_file/ULS_input_file.csv")
    >>> "Family" in table.columns
    True
    """
    warnings.warn(
        "read_input_file is deprecated; use read_uls_input_file instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return read_uls_input_file(file_name)


def read_input_csv(file_name: str | Path) -> pd.DataFrame:
    """Read a UTF-8 CSV input file into a DataFrame.

    Parameters
    ----------
    file_name : str or pathlib.Path
        Path to a file whose extension is ``.csv`` (case-insensitive).

    Returns
    -------
    pandas.DataFrame
        Parsed CSV content.

    Examples
    --------
    >>> table = read_input_csv("tests/input_file/FLS_input_file.csv")
    >>> isinstance(table, pd.DataFrame)
    True
    """
    path = Path(file_name)
    if path.suffix.lower() != ".csv":
        raise ValueError("The input file is not a CSV file, check file_name again")
    return pd.read_csv(path, encoding="utf-8-sig")
