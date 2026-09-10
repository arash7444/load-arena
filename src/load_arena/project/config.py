"""Validated project configuration and input preflight without simulation reads."""

from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, ValidationError, model_validator
import yaml

from load_arena.case_loader.input_reader import (
    read_fls_input_file, read_uls_input_file, validate_case_rows,
)
from load_arena.utils.channels import validate_channels


class ProjectConfigError(ValueError):
    """A project configuration or referenced input is invalid."""


def _nonblank_path(value: object) -> object:
    """Reject blank paths before pathlib converts them to the current directory.

    Parameters
    ----------
    value : object
        Unparsed path value.

    Returns
    -------
    object
        Original nonblank value for Pydantic path validation.

    Examples
    --------
    >>> _nonblank_path("results")
    'results'
    """
    if isinstance(value, str) and not value.strip():
        raise ValueError("Path must not be blank.")
    return value


ProjectPath = Annotated[Path, BeforeValidator(_nonblank_path)]
PositiveNumber = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
ChannelList = Annotated[list[str], BeforeValidator(validate_channels)]


class _ConfigModel(BaseModel):
    """Reject unknown keys in every project section."""

    model_config = ConfigDict(extra="forbid")


class ProjectInfo(_ConfigModel):
    """Campaign identity."""

    name: Annotated[str, Field(strict=True, min_length=1, pattern=r"\S")]


class DataConfig(_ConfigModel):
    """Simulation software and root directory."""

    software: Literal["HAWC2"]
    results_path: ProjectPath


class StatisticsConfig(_ConfigModel):
    """Standalone statistics switch."""

    enabled: StrictBool = False


class ULSConfig(_ConfigModel):
    """ULS switch and CSV location."""

    enabled: StrictBool = False
    cases: ProjectPath | None = None
    channels: Literal["all"] | ChannelList | ProjectPath | None = None


class FLSConfig(_ConfigModel):
    """FLS cases and parameters shared across selected channels."""

    enabled: StrictBool = False
    cases: ProjectPath | None = None
    channels: Literal["all"] | ChannelList | ProjectPath | None = None
    wohler_exponents: Annotated[list[PositiveNumber], Field(min_length=1)] | None = None
    n_ref: PositiveNumber | None = None
    method: Literal["windap", "astm"] = "windap"


class AnalysisConfig(_ConfigModel):
    """Independent analysis sections, disabled when omitted."""

    statistics: StatisticsConfig = Field(default_factory=StatisticsConfig)
    uls: ULSConfig = Field(default_factory=ULSConfig)
    fls: FLSConfig = Field(default_factory=FLSConfig)


class OutputConfig(_ConfigModel):
    """Root directory for generated analysis CSVs."""

    directory: ProjectPath


class ProjectConfig(_ConfigModel):
    """Structured configuration for a complete simulation campaign."""

    project: ProjectInfo
    data: DataConfig
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    output: OutputConfig

    @model_validator(mode="after")
    def _enabled_requirements(self) -> "ProjectConfig":
        """Require inputs for enabled analyses.

        Parameters
        ----------
        self : ProjectConfig
            Structurally validated project configuration.

        Returns
        -------
        ProjectConfig
            Configuration with complete enabled sections.

        Examples
        --------
        >>> config = ProjectConfig.model_validate(document)
        """
        for name in ("uls", "fls"):
            section = getattr(self.analysis, name)
            fields = ("cases", "channels") if name == "uls" else (
                "cases", "channels", "wohler_exponents", "n_ref",
            )
            for field in fields:
                if section.enabled and getattr(section, field) is None:
                    raise ValueError(f"analysis.{name}.{field} is required when enabled.")
        return self


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that also rejects duplicate mapping keys."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        """Construct a mapping without silently replacing duplicate values.

        Parameters
        ----------
        node : yaml.MappingNode
            YAML mapping to construct.
        deep : bool
            Whether nested objects are constructed immediately.

        Returns
        -------
        dict
            Mapping with unique keys.

        Examples
        --------
        >>> yaml.load("name: example", Loader=_UniqueKeyLoader)
        {'name': 'example'}
        """
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in keys:
                    raise yaml.constructor.ConstructorError(
                        "duplicate key", node.start_mark, str(key), key_node.start_mark,
                    )
                keys.add(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "invalid mapping key", node.start_mark, str(key), key_node.start_mark,
                ) from exc
        return super().construct_mapping(node, deep=deep)


def load_config(path: str | Path) -> tuple[Path, ProjectConfig]:
    """Read YAML, validate its structure, and resolve project-relative paths.

    Parameters
    ----------
    path : str or pathlib.Path
        Source YAML filename.

    Returns
    -------
    tuple[pathlib.Path, ProjectConfig]
        Absolute source path and validated configuration.

    Examples
    --------
    >>> source, config = load_config("project.yaml")
    """
    source = Path(path).resolve()
    try:
        with source.open(encoding="utf-8-sig") as stream:
            document = yaml.load(stream, Loader=_UniqueKeyLoader)
        config = ProjectConfig.model_validate(document)
        config.data.results_path = (source.parent / config.data.results_path).resolve()
        config.output.directory = (source.parent / config.output.directory).resolve()
        for section in (config.analysis.uls, config.analysis.fls):
            if section.cases is not None:
                section.cases = (source.parent / section.cases).resolve()
            if isinstance(section.channels, Path):
                channel_path = (source.parent / section.channels).resolve()
                try:
                    table = pd.read_csv(channel_path, dtype=str, keep_default_na=False)
                    if "Channel" not in table.columns:
                        raise ValueError("Channel CSV must contain a 'Channel' column.")
                    section.channels = validate_channels(table["Channel"].tolist())
                except (OSError, UnicodeError, ValueError) as exc:
                    raise ValueError(f"channels ({channel_path}): {exc}") from exc
        if not config.data.results_path.is_dir():
            raise ValueError(f"data.results_path is not a directory: {config.data.results_path}")
        return source, config
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError, ValueError) as exc:
        raise ProjectConfigError(f"{source}: {exc}") from exc


def check_simulation_file(path: Path) -> Path:
    """Resolve a HAWC2 input and check companions without opening sample data.

    Parameters
    ----------
    path : pathlib.Path
        Explicit simulation filename or reader-compatible prefix.

    Returns
    -------
    pathlib.Path
        Explicit supported simulation path with available companion files.

    Examples
    --------
    >>> resolved = check_simulation_file(Path("results/case"))
    """
    path = path.resolve()
    # Match the existing reader's prefix precedence: SEL, INT, then RES.
    if path.suffix.lower() == ".sel":
        selected = path
    elif Path(str(path) + ".sel").is_file():
        selected = Path(str(path) + ".sel")
    elif path.suffix.lower() == ".dat":
        selected = path.with_suffix(".sel")
    elif path.suffix.lower() in {".int", ".res"}:
        selected = path
    else:
        selected = next((Path(str(path) + suffix) for suffix in (".int", ".res")
                         if Path(str(path) + suffix).is_file()), None)
        if selected is None:
            raise ProjectConfigError(f"Missing or unsupported HAWC2 simulation: {path}")
    companion = (selected.with_suffix(".dat") if selected.suffix.lower() == ".sel"
                 else selected.parent / "sensor")
    for required in (selected, companion):
        if not required.is_file():
            raise ProjectConfigError(f"Simulation {path}: missing required file {required}")
    return selected


def load_cases(config: ProjectConfig, mode: Literal["uls", "fls"]) -> pd.DataFrame:
    """Read, validate, and resolve an analysis case table without loading samples.

    Parameters
    ----------
    config : ProjectConfig
        Configuration with resolved YAML paths.
    mode : {"uls", "fls"}
        Analysis whose CSV is read.

    Returns
    -------
    pandas.DataFrame
        Case table with absolute folders and explicit simulation filenames.

    Examples
    --------
    >>> cases = load_cases(project.config, "uls")
    """
    path = getattr(config.analysis, mode).cases
    try:
        reader = read_uls_input_file if mode == "uls" else read_fls_input_file
        table = reader(path)
        validate_case_rows(table, mode)
        for position, (index, row) in enumerate(table.iterrows(), start=2):
            try:
                folder = config.data.results_path / row["Folder"]
                simulation = check_simulation_file(folder / row["Timeseries"])
            except (OSError, ValueError) as exc:
                raise ProjectConfigError(f"CSV row {position}: {exc}") from exc
            table.at[index, "Folder"] = str(simulation.parent)
            table.at[index, "Timeseries"] = simulation.name
        return table
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise ProjectConfigError(f"analysis.{mode}.cases ({path}): {exc}") from exc
