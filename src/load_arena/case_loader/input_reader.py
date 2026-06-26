import pandas as pd
import json
import os
import sys
import pathlib as Path


def read_input_file(file_name:str) -> pd.DataFrame:
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
    df_input = read_input_excel(file_name)

    return df_input


def read_input_excel(file_name):
    
    
    df = pd.read_excel(file_name)

    return df
    


if __name__ == "__main__":
    file_name = r".\tests\input_file\input_file.xlsx"
    df_out = read_input_file(file_name)
    print(df_out.head())
