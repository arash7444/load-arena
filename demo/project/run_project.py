"""Run a portable, illustrative campaign against the checked-in HAWC2 fixtures."""

from load_arena.visualization import statistics_plots
from pathlib import Path

from load_arena import LoadArenaProject


def main() -> None:
    """Load the adjacent YAML and run all three analyses explicitly.

    Parameters
    ----------
    None
        Configuration is read from the script's directory.

    Returns
    -------
    None
        Prints result summaries and writes configured CSV outputs.

    Examples
    --------
    >>> main()
    """
    project = LoadArenaProject.from_yaml(Path(__file__).with_name("project.yaml"))
    statistics = project.run_statistics()
    uls = project.run_uls()
    fls = project.run_fls()
    print(f"Statistics: {len(statistics.filename)} simulations")
    print(uls.ULS)
    for name, channel in fls.channels.items():
        print(name)
        print(channel.files)
        print(channel.campaign)
    print(f"CSV outputs: {project.config.output.directory}")
    # example:
    ch_tmp = fls.channels["Time_[s]"]
    ch_tmp.files
    ch_tmp.rainflow_results
    ch_tmp.campaign



    # statistics.explore(channel="Aerot._[kW]", statistic="mean")


    statistics.explore(
        channel="Aerot._[kW]",
        statistic="max",
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        kind="scatter",
    )
    input("Press enter to exit")


if __name__ == "__main__":
    main()
