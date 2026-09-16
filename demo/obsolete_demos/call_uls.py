import matplotlib.pyplot as plt
from rich.console import Console
from rich.traceback import install

from load_arena.case_loader import read_uls_input_file
from load_arena.process.concatenate_stats import concatenate_stats
from load_arena.process.family_avg import calc_family_avg
from load_arena.process.uls import calc_uls
import pathlib

install()
console = Console()


def first_load_channel(df):
    """
    Return the first load channel column from a ULS DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing ULS values and companion filename columns.

    Returns
    -------
    str
        First channel column that is not metadata and not a filename column.

    Examples
    --------
    >>> import pandas as pd
    >>> first_load_channel(pd.DataFrame({"max_Load": [1.0], "max_Load_filename": ["case"]}))
    'Load'
    """
    for column in df.columns[1::6] if "Family" in df.columns else df.columns[::6]:
        return column[len("max_"):]

    raise ValueError("No load channel column found in the ULS DataFrame.")


def plot_family_uls(family_uls, channel):
    """
    Plot per-family ULS values for one selected channel.

    Parameters
    ----------
    family_uls : pandas.DataFrame
        DataFrame containing one ULS row per family.
    channel : str
        Channel name to plot.

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        Matplotlib figure and axes containing the plot.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({"Family": [1], "AbsMax_Load": [10.0], "AbsMax_Load_filename": ["case"]})
    >>> fig, ax = plot_family_uls(data, "Load")
    >>> plt.close(fig)
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        family_uls["Family"].astype(str),
        family_uls[f"AbsMax_{channel}"],
        color="tab:red",
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.grid(axis="y")
    ax.set_xlabel("Family")
    ax.set_ylabel(channel)
    ax.set_title(f"Family ULS - {channel}")

    for index, row in family_uls.iterrows():
        ax.annotate(            
            pathlib.Path(row[f"AbsMax_{channel}_filename"]).stem,
            xy=(index, row[f"AbsMax_{channel}"]/2),
            #xytext=(0, 5 if row[f"AbsMax_{channel}"] >= 0 else -15),
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            rotation=90,
        )

    fig.tight_layout()
    return fig, ax


file_name = r".\tests\input_file\ULS_input_file.csv"
df_input = read_uls_input_file(file_name)

all_stats_hawc2 = concatenate_stats(input_file_df=df_input)
family_stats = calc_family_avg(all_stats_hawc2, df_input)
uls_stats = calc_uls(family_stats, all_stats_hawc2)

ULS = uls_stats.ULS
Family_ULS = uls_stats.Family_ULS

console.print("Global ULS values: \n", ULS)
console.print("Family ULS values: \n", Family_ULS)

channel_to_plot = "Aerot._[kW]"
if f"AbsMax_{channel_to_plot}" not in Family_ULS.columns:
    channel_to_plot = first_load_channel(Family_ULS)

console.print(f"Plotting ULS channel: {channel_to_plot}")
console.print(
    "Global ULS source filename:",
    ULS[f"AbsMax_{channel_to_plot}_filename"].iloc[0],
)

fig, ax = plot_family_uls(Family_ULS, channel_to_plot)
plt.show(block=False)

console.print("----------------------------------")
input("Press Enter to exit")
plt.close(fig)
