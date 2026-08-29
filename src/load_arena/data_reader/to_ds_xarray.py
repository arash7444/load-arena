import pandas as pd
import xarray as xr
    
from load_arena.data_reader import read_hawc2_flex
from pathlib import Path
    
def to_xarray_dataset(data: pd.DataFrame) -> xr.Dataset:

    df = data.copy()

    # df.index.name = "sample"

    ds = xr.Dataset.from_dataframe(df)


    # print("Dimensions:", ds.sizes)
    # print("Coordinates:", list(ds.coords))
    # print("Data variables:", list(ds.data_vars))
    # print("Global attributes:", ds.attrs)


    # channel = ds["Time_[s]"]
    # print(channel.values)
    # print(channel.dims)
    # print(channel.coords)
    # print(channel.attrs)

    # test = channel.mean()
    # print(test.values)  

    # print(ds)
    return ds


if __name__ == "__main__":

    df_1 = read_hawc2_flex(
        Path(r"d:\Arash_repo\load-arena\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004")
    )

    df_xr = (
        df_1.rename(columns={"Time_[s]": "time"})
            .set_index("time")
    )

    ds = xr.Dataset.from_dataframe(df_xr)


    print(ds)
   
    # print("Dimensions:", ds.sizes)
    # print("Coordinates:", list(ds.coords))
    # print("Data variables:", list(ds.data_vars))
    # print("Global attributes:", ds.attrs)


    # channel = ds["Time_[s]"]

    # first_100_samples = ds.isel(index=slice(0, 100))
    # first_3_samples = ds.isel(index=slice(0, 3))


    print(ds)

    print("Dimensions:", ds.sizes)
    print("Coordinates:", list(ds.coords))
    print("Data variables:", list(ds.data_vars))
    print("Global attributes:", ds.attrs)


    blade_load = ds["blade1N1Mxcoo:_[kNm]"]

    mean_load = blade_load.mean(dim="time")

    print(mean_load.item())

        # Select using physical time labels
    a = blade_load.sel(time=slice(201, 205))

    # Select using integer positions
    b = blade_load.isel(time=slice(2500, 5000))


    channel = ds["blade1N1Mxcoo:_[kNm]"]

    print(channel.mean(dim="time").item())
    print(channel.sel(time=slice(300, 400)))
    
    print("--------------------------")

    for column, unit, description in zip(
        df_1.columns,
        df_1.attrs["units"],
        df_1.attrs["descriptions"],
    ):
        variable = "time" if column == "Time_[s]" else column

        ds[variable].attrs["units"] = unit
        ds[variable].attrs["description"] = description


    channel = ds["blade1N1Mxcoo:_[kNm]"]
    
    print(channel.attrs)
    print(channel.attrs["units"])
    print(channel.attrs["description"])