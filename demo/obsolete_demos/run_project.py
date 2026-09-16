"""Run a portable, illustrative campaign against the checked-in HAWC2 fixtures."""

from load_arena.visualization import statistics_plots
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
    family_stats = uls.family_stats
    
    fls = project.run_fls()
    print(f"Statistics: {len(statistics.filename)} simulations")
    print(uls.ULS)
    # for name, channel in fls.channels.items():
    #     print(name)
    #     print(channel.files)
    #     print(channel.campaign)
    print(f"CSV outputs: {project.config.output.directory}")
    # example:
    ch_tmp = fls.channels["Time_[s]"]
    ch_tmp.files
    ch_tmp.rainflow_results
    ch_tmp.campaign



    """
    Plotting

    """

    fig = statistics.explore(
        channel="Aerot._[kW]",
        statistic="max",
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        kind="scatter",
        show=False,
    )
    fig.update_layout(
        plot_bgcolor="lightgray",  # Inside the axes
        paper_bgcolor="white",    # Outside the axes
    )
    fig.show()


    fig2 = family_stats.explore( 
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        channel="Aerot._[kW]",
        statistic="max",
        plf=False, 
        kind="scatter",
        show=False,
     )

    fig2.update_layout(
        plot_bgcolor="lightgray",  # Inside the axes
        paper_bgcolor="white",    # Outside the axes
    )
    fig2.show()

    fig10 =family_stats.explore(
    x_channel="WSPgl._[m/s]",
    x_statistic="mean",
    x_plf=True,
    channel="Aerot._[kW]",
    statistic="max",
    plf=True,
    )
    fig10.show()

#### Family stat plots
    # fig = family_stats.explore(
    #     x_channel="WSPgl._[m/s]",
    #     x_statistic="mean",
    #     channel="Aerot._[kW]",
    #     statistic="mean",
    #     plf=False,
    # )

    # fig = family_stats.explore(
    # channel="Aerot._[kW]",
    # statistic="max",
    # plf=True,
    # )




    from load_arena import plot

    family_stats = uls.family_stats

    simulation_series = statistics.series(
        channel="Aerot._[kW]",
        statistic="max",
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        name="Simulations",
    )

    family_series = family_stats.series(
        channel="Aerot._[kW]",
        statistic="mean",
        x_channel="WSPgl._[m/s]",
        x_statistic="mean",
        plf=False,
        name="Family average",
    )

    fig3 = plot(simulation_series, family_series, kind="scatter")
    fig3.update_layout(
        plot_bgcolor="lightgray",  # Inside the axes
        paper_bgcolor="white",    # Outside the axes
    )
    fig3.show()



    input("Press enter to exit")
if __name__ == "__main__":
    main()
