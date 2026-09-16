"""Demonstrate LoadArena's current public workflows in one executable script."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import plotly.express as px
from rich.console import Console
from rich.markdown import Markdown
from rich.traceback import install

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

install()
console = Console(markup=False)


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

    console.print(Markdown("# Load project"))
    config_path = Path(__file__).with_name("project.yaml")
    project = LoadArenaProject.from_yaml(config_path)

    console.print(f"Project: {project.config.project.name}")
    console.print(f"Configuration: {project.source_path}")
    console.print(f"Simulation results: {project.config.data.results_path}")
    console.print(f"Output directory: {project.config.output.directory}")
    console.print(f"Simulation software: {project.config.data.software}")
    console.print(
        "Enabled analyses:",
        {
            "statistics": project.config.analysis.statistics.enabled,
            "uls": project.config.analysis.uls.enabled,
            "fls": project.config.analysis.fls.enabled,
        },
    )

    console.print(Markdown("# Statistics"))
    statistics = project.run_statistics()
    console.print(f"Available simulations: {len(statistics.filename)}")
    console.print("First simulation files:")
    console.print(
        *(Path(filename).name for filename in statistics.filename[:3]),
        sep="\n",
    )
    console.print(f"Available channels: {len(statistics.mean.columns)}")
    console.print("First 10 channels:", statistics.mean.columns.tolist()[:10])

    for statistic_name in ("mean", "std", "min", "max"):
        table = getattr(statistics, statistic_name)
        console.print(f"\n{statistic_name} values for {load_channel}:")
        console.print(table[load_channel].head(3))

    console.print("\nRaw and standalone PLF-adjusted statistics:")
    console.print(
        statistics.mean[[load_channel]].head(3).rename(
            columns={load_channel: "raw_mean"}
        ).join(
            statistics.mean_plf[[load_channel]].head(3).rename(
                columns={load_channel: "mean_plf"}
            )
        )
    )
    console.print(
        "Standalone statistics use a factor of 1, so their raw and PLF tables "
        "match. Statistics plotting intentionally has no x_plf option."
    )

    # ``show=False`` lets callers customize a returned figure before display.
    statistics_scatter = statistics.explore(
        channel=load_channel,
        statistic="max",
        kind="scatter",
        show=False,
    )
    statistics_scatter.update_layout(title="Maximum power by simulation row")
    statistics_scatter.show()


    # Display basenames while retaining full paths in the result and custom data.
    statistics_by_file = statistics.explore(
        channel=load_channel,
        statistic="max",
        kind="scatter",
        show=False,
    )
    statistics_by_file.update_traces(
        x=[Path(filename).name for filename in statistics.filename],
    )
    statistics_by_file.update_layout(xaxis_title="Simulation file")
    statistics_by_file.show()

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

    console.print(Markdown("# Family statistics"))
    # ULS retains the exact FamilyAvg object used by its calculation, so no
    # separate family-statistics calculation is necessary.
    uls = project.run_uls()
    family_statistics = uls.family_stats

    console.print("Family identifiers:")
    console.print(family_statistics.family_name)
    for statistic_name in ("mean", "std", "min", "max"):
        raw_table = getattr(family_statistics, statistic_name)
        plf_table = getattr(family_statistics, f"{statistic_name}_plf")
        console.print(f"\nRaw family {statistic_name}:")
        console.print(raw_table[["Family", load_channel]].head(3))
        console.print(f"PLF-adjusted family {statistic_name}:")
        console.print(plf_table[["Family", load_channel]].head(3))

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
    console.print("\nFamily provenance sample:")
    console.print(family_provenance.head(6))
    console.print(
        "Configured averaging methods:",
        sorted(family_provenance["averaging_method"].unique()),
    )
    console.print(
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

    console.print(Markdown("# Combined PlotSeries visualization"))
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
    console.print(
        "Series objects use the public PlotSeries type:",
        isinstance(simulation_series, PlotSeries),
    )
    console.print("First simulation-series metadata row:")
    console.print(simulation_series.metadata[0])
    combined_figure = plot(simulation_series, family_series, kind="scatter")
    combined_figure.show()

    console.print(Markdown("# Ultimate loads"))
    uls_columns = [
        f"{side}_{load_channel}{suffix}"
        for side in ("max", "min", "AbsMax")
        for suffix in ("", "_filename")
    ]
    console.print("Global ULS values and governing sources:")
    console.print(uls.ULS[uls_columns])
    console.print("\nFamily-level ULS values and governing sources:")
    console.print(uls.Family_ULS[["Family", *uls_columns]])
    console.print("\nGlobal ULS provenance:")
    console.print(
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

    console.print(Markdown("# Fatigue loads"))
    fls = project.run_fls()
    console.print(f"Rainflow method: {fls.method}")
    console.print(f"Campaign reference cycles: {fls.n_ref}")
    console.print(f"Available fatigue channels: {len(fls.channels)}")
    console.print("First 10 fatigue channels:", list(fls.channels)[:10])

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
    console.print(f"\nPer-case fatigue results for {load_channel}:")
    console.print(fatigue_channel.files[fatigue_columns])
    console.print("\nCampaign DELs:")
    console.print(fatigue_channel.campaign)
    console.print(
        "Occurrences weight repetitions of the complete simulation. No extra "
        "lifetime normalization or separate FLS provenance object is exposed."
    )

    case_row = int(fatigue_channel.files["case_row"].iloc[0])
    case_result = fatigue_channel.files.set_index("case_row").loc[case_row]
    source_path = Path(case_result["filename"])

    console.print(Markdown("# Data reading"))
    raw_data = read_hawc2_flex(source_path)
    console.print(f"Read {source_path.name}")
    console.print(f"Data shape: {raw_data.shape}")
    console.print("First 10 available channels:")
    console.print(raw_data.columns.tolist()[:10])
    console.print("Representative channel metadata:")
    metadata_names = raw_data.attrs.get("channel_names", [])
    metadata_units = raw_data.attrs.get("units", [])
    metadata_descriptions = raw_data.attrs.get("descriptions", [])
    if metadata_names and metadata_units and metadata_descriptions:
        for channel_name in (time_channel, wind_speed_channel, load_channel):
            channel_position = metadata_names.index(channel_name)
            console.print(
                {
                    "channel": channel_name,
                    "unit": metadata_units[channel_position],
                    "description": metadata_descriptions[channel_position],
                }
            )
    else:
        console.print("No additional channel metadata is exposed.")
    console.print("Representative raw time-series values:")
    console.print(raw_data[[time_channel, load_channel]].head())

    console.print(Markdown("# Rainflow analysis"))
    rainflow = fatigue_channel.rainflow_results[case_row]
    console.print(f"Selected FLS case row: {case_row}")
    console.print(f"Selected source: {source_path.name}")
    console.print(f"Method: {rainflow.method}")
    console.print(f"Windap levels: {rainflow.levels}")
    console.print(f"Windap threshold: {rainflow.threshold}")
    console.print("Cycle table sample:")
    console.print(rainflow.cycles.head())
    console.print("Range sample:", rainflow.range.head().tolist())
    console.print("Mean sample:", rainflow.mean.head().tolist())
    console.print("Count sample:", rainflow.count.head().tolist())

    console.print(Markdown("# Rainflow visualization"))
    # The current range-spectrum plotting helper accepts a raw signal and
    # performs its own rainflow count.
    with redirect_stdout(StringIO()):
        range_spectrum_figure = plot_rainflow_range_spectrum(raw_data[load_channel])
    range_spectrum_figure.show()

    # Damage and matrix calculations can reuse the retained FLS rainflow cycles.
    damage_spectrum = make_damage_range_spectrum(
        rainflow,
        wohler_exponent=wohler_exponent,
        bins=20,
    )
    _, damage_percent = damage_fraction(damage_spectrum)
    console.print("Damage contribution sample (%):", damage_percent[:5])
    damage_figure = plot_damage_ratio(damage_spectrum, damage_percent)
    damage_figure.show()

    rainflow_matrix = make_rainflow_matrix(
        rainflow,
        mean_bins=20,
        range_bins=20,
    )
    console.print(f"Rainflow matrix shape: {rainflow_matrix.count.shape}")
    matrix_figure = plot_rainflow_matrix(rainflow_matrix)
    matrix_figure.show()
    console.print(
        "LoadArena does not currently expose a DEL-versus-wind-speed plotting "
        "API."
    )

    console.print(Markdown("# Time-series visualization"))
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

    console.print(f"\nCSV outputs: {project.config.output.directory}")
    console.print("LoadArena capability demo completed.")


if __name__ == "__main__":
    main()
