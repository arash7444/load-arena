import os
import sys
from pathlib import Path

def find_files(folder_name, file_extension) -> list[Path|str]:
    """
    Find all files with a specific extension in a given folder and its subfolders.

    Parameters:
    -----------
        folder_name: str
            The path to the folder where the search will begin.
        file_extension: str
            The file extension to search for (e.g., '.txt', '.csv').

    Returns:
    --------
        list[Path|str]: A list of Path objects or strings representing the found files.
    """
    found_files = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(file_extension):
                found_files.append(Path(root) / file)
    return found_files
