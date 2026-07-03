import pandas as pd

# import json
import os
from difflib import get_close_matches


REQUIRED_INPUT_COLUMNS = [
    "Folder",
    "Case_folder",
    "Timeseries",
    "Family",
    "PLF",
    "Averaging_method",
]


def validate_input_columns(df: pd.DataFrame) -> None:
    """
    Validate that the user input file has all required columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input file data containing simulation folder, timeseries name, family,
        partial load factor, and averaging method columns.

    Returns
    -------
    None
        The function returns nothing when the input columns are valid.

    Example
    -------
    >>> df_input = pd.DataFrame({
    ...     "Folder": ["tests/h2_res/dlc12/"],
    ...     "Case_folder": ["dlc12"],
    ...     "Timeseries": ["case_001"],
    ...     "Family": [1],
    ...     "PLF": [1.0],
    ...     "Averaging_method": ["mean"],
    ... })
    >>> validate_input_columns(df_input)
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df_input must be a pandas DataFrame.")

    missing_columns = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
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


def read_input_file(file_name: str) -> pd.DataFrame:
    """
    This function call two other functions to read input file provided by user in order to post process simulation files

    Parameters:
    --------
    file_name: str
        the input file can be either be Excel file or Json file

    Returns:
    --------
    df: pandas dataframe
        a data frame containing folder, list of file names, Family number, Partial safety factor, Averaging method


    """

    file_name = file_name
    df_input = read_input_csv(file_name)
    validate_input_columns(df_input)

    return df_input


def read_input_csv(file_name: str) -> pd.DataFrame:
    """
    Parameters:
    -----------
    file_name: str
        csv file name

    Returns:
    -------
    df: Pandas dataframe
        a dataframe from the csv file

    """
    if os.path.splitext(file_name)[1] == ".csv":    
        df = pd.read_csv(file_name, encoding="utf-8-sig")

    else:
        raise ValueError("The input file is not a CSV file, check file_name again")
        

    return df


# def read_json_input(file_name):

#     with file_name.open("r", encoding="utf-8") as file:
#         config = json.load(file)

#     global_config = config["global_config"]
#     timeseries_config = pd.DataFrame(config["timeseries_config"])

#     return global_config, timeseries_config


if __name__ == "__main__":
    file_name = r".\tests\input_file\input_file.csv"
    df_input = read_input_file(file_name)
    print(df_input.head())
