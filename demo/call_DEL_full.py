import matplotlib.pyplot as plt
from rich.console import Console
from rich.traceback import install
import pandas as pd
import numpy as np


from load_arena.data_reader import  Hawc2io, toDataFrame, LoadArenaConfig
from load_arena.process.concatenate_stats import concatenate_stats
from load_arena.process.concatenate_stats import validate_input_columns

from load_arena.process import calculate_rainflow, calc_del
from load_arena.data_reader import read_hawc2_flex, read_hawc2_sel
from load_arena.case_loader import read_fls_input_file
from load_arena.utils import find_files, weibull_probab



install()
console = Console()


file_name = r".\tests\input_file\FLS_input_file.csv"
df_input = read_fls_input_file(file_name)

windspd = np.arange(5,25,1)
A = 10
k = 2
# this is probability of windspeed in each bin
df = weibull_probab(windspd,A,k)
plt.plot(df['windspeed'], df['probability'],marker='o')
plt.xlabel('windspeed')
plt.ylabel('probability')
plt.grid(True)



# if list_files is a DataFrame, extract the file paths
if isinstance(df_input, pd.DataFrame): 
    validate_input_columns(df_input)
    list_files = df_input["Folder"] + df_input["Timeseries"]
    occurrences = list(map(float, df_input["Occurrences"]))



i = -1
for i in range(len(list_files)):
    i = i +1
    console.print(list_files[i])   
    data = read_hawc2_flex(list_files[i])

    # del_1hz_ch = [calc_del(data[ch],wohler_exponent=10, n_ref=600) for ch in data.columns]
    del_1hz = []
    for channel in data.columns:
        print(channel)
        data_ch = data[channel]  
        del_1hz.append(calc_del(data_ch,wohler_exponent=10, n_ref=600))

console.print(del_1hz)
print("---------")
console.print(del_1hz_ch)
plt.show()



    
    
    
    
    