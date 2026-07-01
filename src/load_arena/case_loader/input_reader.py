import pandas as pd

# import json
import os
import sys
import pathlib as Path


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
