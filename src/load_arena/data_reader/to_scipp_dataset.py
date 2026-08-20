import scipp as sc
import pandas as pd

def normalize_unit(unit: str) -> str:
    if unit in ("-", "", "1"):
        return "dimensionless"

    return unit

def to_scipp_dataset(data: pd.DataFrame) -> sc.Dataset:
    names = data.attrs["channel_names"]
    units = data.attrs["units"]
    dataset = sc.Dataset(
        coords={
            "time": sc.array(
                dims=["time"],
                values=data["Time_[s]"].to_numpy(),
                unit="s",
            )
        }
    )

    for name, unit in zip(names, units):
        unit = normalize_unit(unit) # scipp doesn't accept dimensionless unit '-' so we convert it to 'dimensionless'
        dataset[name] = sc.array(
            dims=["time"],
            values=data[name].to_numpy(),
            unit=unit,
        )
    print(dataset)

    return dataset