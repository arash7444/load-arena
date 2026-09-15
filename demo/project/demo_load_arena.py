"""Demonstrate LoadArena's current public workflows in one executable script."""

from pathlib import Path

import plotly.express as px

from load_arena import LoadArenaProject, PlotSeries, plot
from load_arena.data_reader import read_hawc2_flex
from load_arena.process import (
    damage_fraction,
    make_damage_range_spectrum,
    make_rainflow_matrix,
)
from load_arena.visualization import (
    plot_damage_ratio,
    plot_rainflow_matrix,
    plot_rainflow_range_spectrum,
)


def main() -> None:
    """Run the complete LoadArena capability demo against its adjacent project.

    Parameters
    ----------
    None
        The demo uses ``project.yaml`` beside this script.

    Returns
    -------
    None
        Results are printed, figures are displayed, and configured CSVs are
        written beneath the demo project's output directory.

    Examples
    --------
    Run the demo from the repository root:

    >>> # uv run python demo/project/demo_load_arena.py
    """
    load_channel = "Aerot._[kW]"
    wind_speed_channel = "WSPgl._[m/s]"
    time_channel = "Time_[s]"

    # ------------------------------------------------------------------
    # Load project
    # ------------------------------------------------------------------
    print("\n=== Load project ===")
    config_path = Path(__file__).with_name("project.yaml")
    project = LoadArenaProject.from_yaml(config_path)

    print(f"Project: {project.config.project.name}")
    print(f"Configuration: {project.source_path}")
    print(f"Simulation results: {project.config.data.results_path}")
    print(f"Output directory: {project.config.output.directory}")
    print(f"Simulation software: {project.config.data.software}")
    print(
        "Enabled analyses:",
        {
            "statistics": project.config.analysis.statistics.enabled,
            "uls": project.config.analysis.uls.enabled,
            "fls": project.config.analysis.fls.enabled,
        },
    )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    print("\n=== Statistics ===")
    statistics = project.run_statistics()
    print(f"Available simulations: {len(statistics.filename)}")
    print("First simulation files:")
    print(*statistics.filename[:3], sep="\n")
    print(f"Available channels ({len(statistics.mean.columns)} total):")
    print(statistics.mean.columns.tolist())

    for statistic_name in ("mean", "std", "min", "max"):
        table = getattr(statistics, statistic_name)
        print(f"\n{statistic_name} values for {load_channel}:")
        print(table[load_channel].head(3))

    print("\nRaw and standalone PLF-adjusted statistics:")
    print(
        statistics.mean[[load_channel]].head(3).rename(
            columns={load_channel: "raw_mean"}
        ).join(
            statistics.mean_plf[[load_channel]].head(3).rename(
                columns={load_channel: "mean_plf"}
            )
        )
    )
    print(
        "Standalone statistics use a factor of 1, so their raw and PLF tables "
        "match. Statistics plotting intentionally has no x_plf option."
    )

    # Default x uses the stored simulation row positions. Constructing with
    # show=False is useful when a caller wants to customize before display.
    statistics_scatter = statistics.explore(
        channel=load_channel,
        statistic="max",
        kind="scatter",
        show=False,
    )
    statistics_scatter.update_layout(title="Maximum power by simulation row")
    statistics_scatter.show()

    # A numeric x channel may use a statistic independent of the y statistic.
    statistics_bar = statistics.explore(
        channel=load_channel,
        statistic="max",
        x_channel=wind_speed_channel,
        x_statistic="mean",
        kind="bar",
        show=False,
    )
    statistics_bar.show()

    statistics_line = statistics.explore(
        channel=load_channel,
        statistic="mean",
        x_channel=wind_speed_channel,
        x_statistic="max",
        kind="line",
        show=False,
    )
    statistics_line.show()

    # ------------------------------------------------------------------
    # Family statistics
    # ------------------------------------------------------------------
    print("\n=== Family statistics ===")
    # ULS retains the exact FamilyAvg object used by its calculation, so no
    # separate family-statistics calculation is necessary.
    uls = project.run_uls()
    family_statistics = uls.family_stats

    print("Family identifiers:")
    print(family_statistics.family_name)
    for statistic_name in ("mean", "std", "min", "max"):
        raw_table = getattr(family_statistics, statistic_name)
        plf_table = getattr(family_statistics, f"{statistic_name}_plf")
        print(f"\nRaw family {statistic_name}:")
        print(raw_table[["Family", load_channel]].head(3))
        print(f"PLF-adjusted family {statistic_name}:")
        print(plf_table[["Family", load_channel]].head(3))

    family_provenance = family_statistics.provenance.loc[
        family_statistics.provenance["channel"] == load_channel,
        [
            "Family",
            "statistic",
            "plf_adjusted",
            "value",
            "averaging_method",
            "member_count",
            "member_files",
            "contributing_files",
            "source_file",
        ],
    ]
    print("\nFamily provenance sample:")
    print(family_provenance.head(6))
    print(
        "Configured averaging methods:",
        sorted(family_provenance["averaging_method"].unique()),
    )
    print(
        "LoadArena also supports mean_half, but this demo configuration does "
        "not select it."
    )

    # The default categorical x axis uses family identifiers.
    family_scatter = family_statistics.explore(
        channel=load_channel,
        statistic="max",
        plf=False,
        kind="scatter",
        show=False,
    )
    family_scatter.show()

    # x_plf and plf can be selected independently for numeric channel axes.
    family_bar = family_statistics.explore(
        channel=load_channel,
        statistic="max",
        plf=True,
        x_channel=wind_speed_channel,
        x_statistic="mean",
        x_plf=False,
        kind="bar",
        show=False,
    )
    family_bar.show()

    family_line = family_statistics.explore(
        channel=load_channel,
        statistic="mean",
        plf=False,
        x_channel=wind_speed_channel,
        x_statistic="max",
        x_plf=True,
        kind="line",
        show=False,
    )
    family_line.show()

    # ------------------------------------------------------------------
    # Combined PlotSeries visualization
    # ------------------------------------------------------------------
    print("\n=== Combined PlotSeries visualization ===")
    simulation_series = statistics.series(
        channel=load_channel,
        statistic="max",
        x_channel=wind_speed_channel,
        x_statistic="mean",
        name="Simulations",
    )
    family_series = family_statistics.series(
        channel=load_channel,
        statistic="mean",
        x_channel=wind_speed_channel,
        x_statistic="mean",
        plf=False,
        name="Family averages",
    )
    print(
        "Series objects use the public PlotSeries type:",
        isinstance(simulation_series, PlotSeries),
    )
    print("First simulation-series metadata row:")
    print(simulation_series.metadata[0])
    combined_figure = plot(simulation_series, family_series, kind="scatter")
    combined_figure.show()

    # ------------------------------------------------------------------
    # Ultimate loads
    # ------------------------------------------------------------------
    print("\n=== Ultimate loads ===")
    uls_columns = [
        f"{side}_{load_channel}{suffix}"
        for side in ("max", "min", "AbsMax")
        for suffix in ("", "_filename")
    ]
    print("Global ULS values and governing sources:")
    print(uls.ULS[uls_columns])
    print("\nFamily-level ULS values and governing sources:")
    print(uls.Family_ULS[["Family", *uls_columns]])
    print("\nGlobal ULS provenance:")
    print(
        uls.global_provenance.loc[
            uls.global_provenance["channel"] == load_channel,
            [
                "side",
                "governing_side",
                "value",
                "Family",
                "averaging_method",
                "member_files",
                "contributing_files",
                "source_file",
            ],
        ]
    )

    # ------------------------------------------------------------------
    # Fatigue loads
    # ------------------------------------------------------------------
    print("\n=== Fatigue loads ===")
    fls = project.run_fls()
    print(f"Rainflow method: {fls.method}")
    print(f"Campaign reference cycles: {fls.n_ref}")
    print(f"Available fatigue channels ({len(fls.channels)} total):")
    print(list(fls.channels))

    fatigue_channel = fls.channels[load_channel]
    exponents = fatigue_channel.campaign["wohler_exponent"].tolist()
    wohler_exponent = 10.0 if 10.0 in exponents else float(exponents[0])
    exponent_label = repr(wohler_exponent).removesuffix(".0")
    fatigue_columns = [
        "case_row",
        "filename",
        "occurrences",
        "duration_s",
        f"DEL_m{exponent_label}",
        f"DEL_1Hz_m{exponent_label}",
    ]
    print(f"\nPer-case fatigue results for {load_channel}:")
    print(fatigue_channel.files[fatigue_columns])
    print("\nCampaign DELs:")
    print(fatigue_channel.campaign)
    print(
        "Occurrences weight repetitions of the complete simulation. No extra "
        "lifetime normalization or separate FLS provenance object is exposed."
    )

    case_row = int(fatigue_channel.files["case_row"].iloc[0])
    case_result = fatigue_channel.files.set_index("case_row").loc[case_row]
    source_path = Path(case_result["filename"])

    # ------------------------------------------------------------------
    # Data reading
    # ------------------------------------------------------------------
    print("\n=== Data reading ===")
    raw_data = read_hawc2_flex(source_path)
    print(f"Read {source_path}")
    print(f"Data shape: {raw_data.shape}")
    print("Available channels:")
    print(raw_data.columns.tolist())
    print("Representative channel metadata:")
    metadata_names = raw_data.attrs.get("channel_names", [])
    metadata_units = raw_data.attrs.get("units", [])
    metadata_descriptions = raw_data.attrs.get("descriptions", [])
    if metadata_names and metadata_units and metadata_descriptions:
        for channel_name in (time_channel, wind_speed_channel, load_channel):
            channel_position = metadata_names.index(channel_name)
            print(
                {
                    "channel": channel_name,
                    "unit": metadata_units[channel_position],
                    "description": metadata_descriptions[channel_position],
                }
            )
    else:
        print("No additional channel metadata is exposed.")
    print("Representative raw time-series values:")
    print(raw_data[[time_channel, load_channel]].head())

    # ------------------------------------------------------------------
    # Rainflow analysis
    # ------------------------------------------------------------------
    print("\n=== Rainflow analysis ===")
    rainflow = fatigue_channel.rainflow_results[case_row]
    print(f"Selected FLS case row: {case_row}")
    print(f"Selected source: {source_path}")
    print(f"Method: {rainflow.method}")
    print(f"Windap levels: {rainflow.levels}")
    print(f"Windap threshold: {rainflow.threshold}")
    print("Cycle table sample:")
    print(rainflow.cycles.head())
    print("Range sample:", rainflow.range.head().tolist())
    print("Mean sample:", rainflow.mean.head().tolist())
    print("Count sample:", rainflow.count.head().tolist())

    # ------------------------------------------------------------------
    # Rainflow visualization
    # ------------------------------------------------------------------
    print("\n=== Rainflow visualization ===")
    # The current range-spectrum plotting helper accepts a raw signal and
    # performs its own rainflow count.
    range_spectrum_figure = plot_rainflow_range_spectrum(raw_data[load_channel])
    range_spectrum_figure.show()

    # Damage and matrix calculations can reuse the retained FLS rainflow cycles.
    damage_spectrum = make_damage_range_spectrum(
        rainflow,
        wohler_exponent=wohler_exponent,
        bins=20,
    )
    _, damage_percent = damage_fraction(damage_spectrum)
    print("Damage contribution sample (%):", damage_percent[:5])
    damage_figure = plot_damage_ratio(damage_spectrum, damage_percent)
    damage_figure.show()

    rainflow_matrix = make_rainflow_matrix(
        rainflow,
        mean_bins=20,
        range_bins=20,
    )
    print(f"Rainflow matrix shape: {rainflow_matrix.count.shape}")
    matrix_figure = plot_rainflow_matrix(rainflow_matrix)
    matrix_figure.show()
    print(
        "LoadArena does not currently expose a DEL-versus-wind-speed plotting "
        "API."
    )

    # ------------------------------------------------------------------
    # Time-series visualization
    # ------------------------------------------------------------------
    print("\n=== Time-series visualization ===")
    # LoadArena currently provides the reader, while this time-series figure is
    # created directly with Plotly rather than a LoadArena-native plotting API.
    time_series_figure = px.line(
        raw_data,
        x=time_channel,
        y=load_channel,
        title=f"{load_channel} — {source_path.name}",
    )
    # Keep the complete path available for future interactions without showing
    # it in user-facing figure labels or hover text.
    time_series_figure.update_traces(meta={"source_path": str(source_path)})
    time_series_figure.show()

    print(f"\nCSV outputs: {project.config.output.directory}")
    print("LoadArena capability demo completed.")


if __name__ == "__main__":
    main()
