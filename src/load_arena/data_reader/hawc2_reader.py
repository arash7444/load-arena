# import wetb
import pkgutil
import inspect
from Hawc2io import ReadHawc2
import pandas as pd

# help(wetb)
data = ReadHawc2(
    r"e:\Projects\Projects\HAWC2_sims\W4000_130\res\dlc13\dlc13_wsp04_wdir000_s023004"
)
res_file = data.ReadFLEX()
sensor_data = data.ChInfo
print(res_file)

df = pd.DataFrame(res_file, columns=sensor_data[0][1:])
df.insert(0, "Time", data.t)

print(df.head())
# for module in pkgutil.iter_modules(wetb.__path__):
#     print(module.name)
