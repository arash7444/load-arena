"""Run a portable, illustrative campaign against the checked-in HAWC2 fixtures."""

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
    print(fls.campaign)
    print(f"CSV outputs: {project.config.output.directory}")


if __name__ == "__main__":
    main()
