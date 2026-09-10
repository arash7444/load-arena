"""Explicit project operations over Load Arena's existing calculation modules."""

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from load_arena.process.concatenate_stats import All_stats, concatenate_stats
from load_arena.process.family_avg import calc_family_avg
from load_arena.process.fls import FLSResult, calc_fls
from load_arena.process.uls import ULSStats, calc_uls
from load_arena.project.config import (
    ProjectConfig, ProjectConfigError, check_simulation_file, load_cases, load_config,
)
from load_arena.utils.find_files import find_files


@dataclass
class LoadArenaProject:
    """One turbine/model campaign with independent, explicitly invoked analyses."""

    config: ProjectConfig
    source_path: Path

    @classmethod
    def from_yaml(cls, path: str | Path) -> "LoadArenaProject":
        """Load configuration and preflight enabled CSVs without loading samples.

        Parameters
        ----------
        path : str or pathlib.Path
            YAML file; its directory anchors all relative YAML paths.

        Returns
        -------
        LoadArenaProject
            Project ready for explicit analysis calls, with no outputs created.

        Examples
        --------
        >>> project = LoadArenaProject.from_yaml("project.yaml")
        """
        source, config = load_config(path)
        for mode in ("uls", "fls"):
            if getattr(config.analysis, mode).enabled:
                load_cases(config, mode)
        return cls(config=config, source_path=source)

    def _require_enabled(self, analysis: str) -> None:
        """Guard an explicit operation with its configured enabled flag.

        Parameters
        ----------
        analysis : str
            Analysis section name.

        Returns
        -------
        None
            Raises ProjectConfigError when disabled.

        Examples
        --------
        >>> project._require_enabled("uls")
        """
        if not getattr(self.config.analysis, analysis).enabled:
            raise ProjectConfigError(f"analysis.{analysis}.enabled is false in {self.source_path}")

    def _write_tables(self, analysis: str, tables: dict[str, pd.DataFrame]) -> None:
        """Write known CSV outputs while preserving unrelated files.

        Parameters
        ----------
        analysis : str
            Output subdirectory.
        tables : dict[str, pandas.DataFrame]
            Table names, without extensions, and their computed values.

        Returns
        -------
        None
            Output errors propagate with the analysis directory as context.

        Examples
        --------
        >>> project._write_tables("uls", {"global": result.ULS})
        """
        directory = self.config.output.directory / analysis
        try:
            directory.mkdir(parents=True, exist_ok=True)
            for name, table in tables.items():
                table.to_csv(directory / f"{name}.csv", index=False)
        except OSError as exc:
            raise OSError(f"Cannot write {analysis} outputs to {directory}: {exc}") from exc

    def run_statistics(self) -> All_stats:
        """Calculate statistics for all supported result files and export CSVs.

        Parameters
        ----------
        self : LoadArenaProject
            Project with statistics enabled.

        Returns
        -------
        All_stats
            Existing raw and PLF statistics with source filenames.

        Examples
        --------
        >>> statistics = project.run_statistics()
        """
        self._require_enabled("statistics")
        files = sorted({Path(file).resolve() for suffix in (".int", ".res", ".sel")
                        for file in find_files(self.config.data.results_path, suffix)})
        if not files:
            raise ProjectConfigError(f"No supported HAWC2 results in {self.config.data.results_path}")
        files = [check_simulation_file(file) for file in files]
        result = concatenate_stats(files)
        tables = {}
        for name in ("mean", "std", "min", "max"):
            table = getattr(result, name).copy()
            table.insert(0, "filename", result.filename)
            tables[name] = table
        self._write_tables("statistics", tables)
        return result

    def run_uls(self) -> ULSStats:
        """Calculate ULS and export a global channel table and family rankings.

        Parameters
        ----------
        self : LoadArenaProject
            Project with ULS enabled and a configured case CSV.

        Returns
        -------
        ULSStats
            Global and per-family min, max, and signed AbsMax values with source
            attribution. CSVs contain one global row per channel and independent
            family rankings in a separate, safely named file per channel.

        Examples
        --------
        >>> uls = project.run_uls()
        """
        self._require_enabled("uls")
        cases = load_cases(self.config, "uls")
        statistics = concatenate_stats(cases, channels=self.config.analysis.uls.channels)
        result = calc_uls(calc_family_avg(statistics, cases), statistics)
        channels = [column[len("max_"):] for column in result.ULS.columns[::6]]
        global_rows = []
        tables = {}
        used_names = {"global", "family"}
        for channel in channels:
            global_row = {"ChannelName_ULS": channel}
            for side, label in (("min", "Min"), ("max", "Max"), ("AbsMax", "AbsMax")):
                global_row[f"{label}_Ultimate_incl_psf"] = result.ULS[f"{side}_{channel}"].iloc[0]
                global_row[f"{label}_fileName"] = result.ULS[f"{side}_{channel}_filename"].iloc[0]
            global_rows.append(global_row)

            ranked = {}
            for side, label in (("max", "Max"), ("min", "Min"), ("AbsMax", "AbsMax")):
                key = f"{side}_{channel}"
                values = result.Family_ULS[key]
                order = (values.abs() if side == "AbsMax" else values).sort_values(
                    ascending=side == "min", kind="stable",
                ).index
                families = result.Family_ULS.loc[order]
                ranked[f"{label} {'Value' if side == 'min' else 'value'}"] = families[key].tolist()
                ranked[f"{label} Family"] = families["Family"].tolist()
                ranked[f"{label} filename"] = families[f"{key}_filename"].tolist()

            stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", channel).rstrip(" .") or "channel"
            if stem.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }:
                stem = f"_{stem}"
            name = stem
            suffix = 2
            while name.casefold() in used_names:
                name = f"{stem}__{suffix}"
                suffix += 1
            used_names.add(name.casefold())
            tables[name] = pd.DataFrame(ranked)
        tables = {"global": pd.DataFrame(global_rows), **tables}
        self._write_tables("uls", tables)
        return result

    def run_fls(self) -> FLSResult:
        """Calculate and export selected channels for every configured exponent.

        Parameters
        ----------
        self : LoadArenaProject
            Project with FLS enabled and complete fatigue parameters.

        Returns
        -------
        FLSResult
            Per-case and campaign DELs identified by channel and exponent.

        Examples
        --------
        >>> fls = project.run_fls()
        """
        self._require_enabled("fls")
        cases = load_cases(self.config, "fls")
        settings = self.config.analysis.fls
        result = calc_fls(cases, settings.wohler_exponents, settings.n_ref, settings.method,
                          channels=settings.channels)
        tables = {name: getattr(result, name).assign(n_ref=result.n_ref, method=result.method)
                  for name in ("per_case", "campaign")}
        self._write_tables("fls", tables)
        return result
