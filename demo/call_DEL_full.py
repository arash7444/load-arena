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

wohlmer_m = 10.0
n_ref = 1e7


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



channel_list =['blade1N1Mxcoo:_[kNm]','blade1N1Mycoo:_[kNm]','blade1N1Mzcoo:_[kNm]','DLLinp_[-]__4']
DEL_lifetime_array = np.zeros(len(channel_list))

for i in range(len(list_files)):

    console.print(list_files[i])   
    data = read_hawc2_flex(list_files[i])

    del_1hz_ch = [calc_del(data[ch],wohler_exponent=wohlmer_m, n_ref=600) for ch in channel_list] # Calculate 1 Hz DEL for each channel 
    DEL_lifetime_array[i] = (np.sum((np.asarray(del_1hz_ch)**wohlmer_m * occurrences)/n_ref))**(1/wohlmer_m) # calculate life time DEL


    # del_1hz = []
    # for channel in channel_list:
    #     print(channel)
    #     data_ch = data[channel]  
    #     del_1hz.append(calc_del(data_ch,wohler_exponent=10, n_ref=600))

# console.print(del_1hz)
print("---------")
console.print(del_1hz_ch)
plt.show()

# DEL_lifetime_array = np.zeros(len(channel_list))
# for i in range(len(channel_list)):
#     DEL_lifetime_array[i] = (np.sum((del_1hz_ch[i]**wohlmer_m) * occurrences)/n_ref)**(1/wohlmer_m)

    


console.print(DEL_lifetime_array)


    
    
    
    
    