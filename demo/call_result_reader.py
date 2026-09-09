    
from load_arena.data_reader import read_hawc2_flex

from load_arena.data_reader import LoadArenaConfig
from load_arena.data_reader import ReadHawc2
from load_arena.data_reader import toDataFrame
from load_arena.process.simple_stats import calc_stats
from load_arena.utils import find_files
from load_arena.process.concatenate_stats import All_stats, concatenate_stats
from load_arena.case_loader import read_uls_input_file

from load_arena.data_reader import to_xarray_dataset, to_scipp_dataset

from rich.console import Console
console = Console()


qblade_folder = r"d:\Projects\Simulation_results\Qblade\IEA_22MW_Offshore_Wind_Turbine_in_Fixed_Bottom_Configuration_Turb"
list_files = find_files(folder_name=qblade_folder, file_extension=".sel")


# hawc2_folder = r".\tests\h2_res\dlc13"
# list_files = find_files(folder_name=hawc2_folder, file_extension=".int")


# file_flex = r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004" # hawc2 flex result file
for files in list_files:    
    res_file = ReadHawc2(files) # Read flex result into data frame
    data = res_file.ReadAll()  
    info = res_file.ChInfo 
    df = toDataFrame(data, info) # Convert data to pandas Dataframe

    # ds = to_xarray_dataset(df) # Convert data to xarray Dataset
    # sc = to_scipp_dataset(df) # Convert data to scipp Dataset
    
    console.print("----------------------------------")
    console.print("Dataframe Data")
    console.print("----------------------------------")
    console.print(df.head()) # Print pandas DataFrame


    console.print("----------------------------------------------------------------")
    console.print("xarray Dataset:")
    console.print("----------------------------------------------------------------")
    # console.print(ds.head()) # Print xarray Dataset
    
    console.print("----------------------------------------------------------------")
    console.print("scipp Dataset:")
    console.print("----------------------------------------------------------------")
    # console.print(sc) # Print scipp Dataset

    print("done")