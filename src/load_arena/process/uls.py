from dataclasses import dataclass, field, replace

import pandas as pd

from load_arena.data_reader.Hawc2io import _make_unique_columns
from load_arena.process.concatenate_stats import All_stats
from load_arena.process.family_avg import FamilyAvg


@dataclass
class ULSStats:
    """Store global, per-family, and source family-average ULS results.

    Parameters
    ----------
    ULS : pandas.DataFrame
        One-row global ULS result.
    Family_ULS : pandas.DataFrame
        Per-family ULS values and source attribution.
    family_stats : FamilyAvg or None, default None
        Original family-average input when produced by ``calc_uls``. The default
        preserves legacy direct construction.
    global_provenance : pandas.DataFrame, optional
        Governing family and structured contributor metadata for global results.

    Returns
    -------
    ULSStats
        Container exposing all ULS result levels.

    Examples
    --------
    >>> result = ULSStats(ULS=global_table, Family_ULS=family_table)
    >>> result.family_stats is None
    True
    """

    ULS: pd.DataFrame
    Family_ULS: pd.DataFrame
    family_stats: FamilyAvg | None = None
    global_provenance: pd.DataFrame = field(default_factory=pd.DataFrame)


def _channel_columns(df: pd.DataFrame) -> list[str]:
    """
    Return load channel columns from a statistics DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Statistics DataFrame that may include metadata columns such as ``Family``.

    Returns
    -------
    list[str]
        Column names that should be included in ULS calculations.

    Examples
    --------
    >>> _channel_columns(pd.DataFrame({"Family": [1], "Load": [3.0]}))
    ['Load']
    """
    return [column for column in df.columns if column != "Family"]


def _copy_with_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of a DataFrame with unique column names.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame whose columns may contain duplicate channel labels.

    Returns
    -------
    pd.DataFrame
        Copy of the input DataFrame with duplicate columns suffixed using
        ``__2``, ``__3``, and so on.

    Examples
    --------
    >>> df = pd.DataFrame([[1.0, 2.0]], columns=["Load", "Load"])
    >>> _copy_with_unique_columns(df).columns.tolist()
    ['Load', 'Load__2']
    """
    unique_df = df.copy()
    unique_df.columns = _make_unique_columns(list(unique_df.columns))
    return unique_df


def _normalize_duplicate_columns(
    family_stats: FamilyAvg,
    all_stats: All_stats,
) -> tuple[FamilyAvg, All_stats]:
    """
    Create stats objects with unique PLF min and max column names.

    Parameters
    ----------
    family_stats : FamilyAvg
        Family-level statistics that may contain duplicate PLF channel columns.
    all_stats : All_stats
        Per-simulation statistics that may contain duplicate PLF channel columns.

    Returns
    -------
    tuple[FamilyAvg, All_stats]
        Copies of the input dataclasses with unique ``min_plf`` and ``max_plf``
        column names used by the ULS calculation.

    Examples
    --------
    >>> family_stats = FamilyAvg(
    ...     mean=pd.DataFrame(), std=pd.DataFrame(), min=pd.DataFrame(),
    ...     max=pd.DataFrame(), mean_plf=pd.DataFrame(), std_plf=pd.DataFrame(),
    ...     min_plf=pd.DataFrame([[1.0, 2.0]], columns=["Load", "Load"]),
    ...     max_plf=pd.DataFrame([[3.0, 4.0]], columns=["Load", "Load"]),
    ...     filename=[], family_name=[], case_folder=[],
    ... )
    >>> all_stats = All_stats(
    ...     mean=pd.DataFrame(), std=pd.DataFrame(), min=pd.DataFrame(),
    ...     max=pd.DataFrame(), mean_plf=pd.DataFrame(), std_plf=pd.DataFrame(),
    ...     min_plf=pd.DataFrame([[1.0, 2.0]], columns=["Load", "Load"]),
    ...     max_plf=pd.DataFrame([[3.0, 4.0]], columns=["Load", "Load"]),
    ...     filename=["case_001"], family=[1],
    ... )
    >>> normalized_family, _ = _normalize_duplicate_columns(family_stats, all_stats)
    >>> normalized_family.min_plf.columns.tolist()
    ['Load', 'Load__2']
    """
    return (
        replace(
            family_stats,
            min_plf=_copy_with_unique_columns(family_stats.min_plf),
            max_plf=_copy_with_unique_columns(family_stats.max_plf),
        ),
        replace(
            all_stats,
            min_plf=_copy_with_unique_columns(all_stats.min_plf),
            max_plf=_copy_with_unique_columns(all_stats.max_plf),
        ),
    )


def _choose_extreme(min_value: float, max_value: float) -> tuple[float, str]:
    """
    Select the signed value with the largest absolute magnitude.

    Parameters
    ----------
    min_value : float
        Candidate minimum value for a channel.
    max_value : float
        Candidate maximum value for a channel.

    Returns
    -------
    tuple[float, str]
        Selected signed ULS value and the side that produced it: ``"min"`` or
        ``"max"``. The max side is selected when absolute magnitudes are equal.

    Examples
    --------
    >>> _choose_extreme(-12.0, 9.0)
    (-12.0, 'min')
    >>> _choose_extreme(-4.0, 4.0)
    (4.0, 'max')
    """
    if abs(min_value) > abs(max_value):
        return min_value, "min"
    return max_value, "max"


def _family_value_provenance(
    family_stats: FamilyAvg,
    family: object,
    statistic: str,
    channel_position: int,
) -> dict | None:
    """Return structured provenance for one stored family-level result.

    Parameters
    ----------
    family_stats : FamilyAvg
        Processed family statistics with optional long-form provenance.
    family : object
        Family identifier for the result row.
    statistic : str
        Statistic name, normally ``"min"`` or ``"max"``.
    channel_position : int
        Zero-based channel position excluding the Family column.

    Returns
    -------
    dict or None
        Matching provenance record, or None for legacy objects without metadata.

    Examples
    --------
    >>> record = _family_value_provenance(family_stats, 1, "max", 0)
    """
    provenance = family_stats.provenance
    required = {"Family", "statistic", "plf_adjusted", "channel_position"}
    if provenance.empty or not required.issubset(provenance.columns):
        return None
    matches = provenance.loc[
        (provenance["Family"] == family)
        & (provenance["statistic"] == statistic)
        & provenance["plf_adjusted"].astype(bool)
        & (provenance["channel_position"] == channel_position)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one PLF provenance record for family {family!r}, "
            f"statistic {statistic!r}, channel position {channel_position}."
        )
    return matches.iloc[0].to_dict()


def _build_family_uls(family_stats: FamilyAvg) -> pd.DataFrame:
    """
    Build one PLF-based ULS row per family.

    Parameters
    ----------
    family_stats : FamilyAvg
        Family-level statistics containing ``min_plf`` and ``max_plf`` tables.
    Returns
    -------
    pd.DataFrame
        Family ULS table with a leading ``Family`` column and ``max_<channel>``,
        ``min_<channel>``, and ``AbsMax_<channel>`` values, each accompanied by
        a ``_filename`` column. Filenames exist only for unique exact sources.

    Examples
    --------
    >>> # See calc_uls for an end-to-end example.
    """
    rows = []
    channels = _channel_columns(family_stats.min_plf)

    for row_index, min_row in family_stats.min_plf.iterrows():
        max_row = family_stats.max_plf.loc[row_index]
        family = min_row["Family"]
        row = {"Family": family}

        for channel_position, channel in enumerate(channels):
            for side, source_row in (("max", max_row), ("min", min_row)):
                value = source_row[channel]
                row[f"{side}_{channel}"] = value
                provenance = _family_value_provenance(
                    family_stats, family, side, channel_position,
                )
                row[f"{side}_{channel}_filename"] = (
                    None if provenance is None else provenance["source_file"]
                )
            value, side = _choose_extreme(min_row[channel], max_row[channel])
            row[f"AbsMax_{channel}"] = value
            row[f"AbsMax_{channel}_filename"] = row[f"{side}_{channel}_filename"]

        rows.append(row)

    result = pd.DataFrame(rows)
    for column in result.columns:
        if column.endswith("_filename"):
            filenames = result[column].astype(object)
            result[column] = filenames.where(filenames.notna(), None)
    return result


def _build_global_provenance(
    family_uls: pd.DataFrame,
    family_stats: FamilyAvg,
) -> pd.DataFrame:
    """Build structured provenance for every global ULS channel and side.

    Parameters
    ----------
    family_uls : pandas.DataFrame
        Processed family ULS candidates used by the global calculation.
    family_stats : FamilyAvg
        Family result containing per-value provenance.

    Returns
    -------
    pandas.DataFrame
        Long-form global max, min, and signed AbsMax provenance.

    Examples
    --------
    >>> provenance = _build_global_provenance(family_uls, family_stats)
    """
    records = []
    channels = [column[len("max_"):] for column in family_uls.columns[1::6]]
    for channel_position, channel in enumerate(channels):
        side_records = {}
        for side in ("max", "min"):
            key = f"{side}_{channel}"
            values = family_uls[key]
            source_index = values.idxmax() if side == "max" else values.idxmin()
            family = family_uls.loc[source_index, "Family"]
            family_record = _family_value_provenance(
                family_stats, family, side, channel_position,
            )
            record = {
                "channel": channel,
                "side": side,
                "governing_side": side,
                "value": family_uls.loc[source_index, key],
                "Family": family,
                "averaging_method": None,
                "member_count": None,
                "member_files": tuple(),
                "contributing_files": tuple(),
                "source_file": family_uls.loc[source_index, f"{key}_filename"],
            }
            if family_record is not None:
                for field_name in (
                    "averaging_method", "member_count", "member_files",
                    "contributing_files", "source_file",
                ):
                    record[field_name] = family_record[field_name]
            records.append(record)
            side_records[side] = record

        _, governing_side = _choose_extreme(
            side_records["min"]["value"], side_records["max"]["value"],
        )
        abs_record = dict(side_records[governing_side])
        abs_record["side"] = "AbsMax"
        abs_record["governing_side"] = governing_side
        records.append(abs_record)
    result = pd.DataFrame(records)
    if "source_file" in result:
        source_files = result["source_file"].astype(object)
        result["source_file"] = source_files.where(source_files.notna(), None)
    return result


def _build_global_uls(family_uls: pd.DataFrame) -> pd.DataFrame:
    """
    Build the global ULS row from family-level ULS values.

    Parameters
    ----------
    family_uls : pd.DataFrame
        Family ULS table with separate max, min, and signed AbsMax values and
        matching filename columns for each channel.

    Returns
    -------
    pd.DataFrame
        One-row global ULS table without ``Family``, selecting the largest max,
        smallest min, and signed absolute extreme independently per channel.
        Equal absolute magnitudes prefer max; same-side ties use the first family.

    Examples
    --------
    >>> family_uls = pd.DataFrame({
    ...     "Family": [1, 2], "max_Load": [2.0, 3.0],
    ...     "max_Load_filename": ["a", "b"], "min_Load": [-4.0, -2.0],
    ...     "min_Load_filename": ["a", "b"],
    ...     "AbsMax_Load": [-4.0, 3.0], "AbsMax_Load_filename": ["a", "b"],
    ... })
    >>> _build_global_uls(family_uls)["AbsMax_Load"].iloc[0]
    -4.0
    """
    row = {}
    channels = [
        column[len("max_"):]
        for column in family_uls.columns[1::6]
    ]

    for channel in channels:
        for side in ("max", "min"):
            key = f"{side}_{channel}"
            values = family_uls[key]
            source_index = values.idxmax() if side == "max" else values.idxmin()
            row[key] = family_uls.loc[source_index, key]
            row[f"{key}_filename"] = family_uls.loc[source_index, f"{key}_filename"]
        value, side = _choose_extreme(row[f"min_{channel}"], row[f"max_{channel}"])
        row[f"AbsMax_{channel}"] = value
        row[f"AbsMax_{channel}_filename"] = row[f"{side}_{channel}_filename"]

    result = pd.DataFrame([row])
    for column in result.columns:
        if column.endswith("_filename"):
            filenames = result[column].astype(object)
            result[column] = filenames.where(filenames.notna(), None)
    return result


def calc_uls(family_stats: FamilyAvg, all_stats: All_stats) -> ULSStats:
    """
    Calculate PLF-based Ultimate Load / ULS values.

    Parameters
    ----------
    family_stats : FamilyAvg
        Family-level statistics returned by ``calc_family_avg``. The calculation
        uses ``min_plf`` and ``max_plf`` only.
    all_stats : All_stats
        Per-simulation statistics returned by ``concatenate_stats``, retained in
        the public signature for compatibility. Its values and filenames never
        recalculate or attribute family results.

    Returns
    -------
    ULSStats
        Dataclass containing global ``ULS``, per-family ``Family_ULS``, and the
        original ``family_stats`` input plus structured global provenance.

    Examples
    --------
    >>> family_stats = calc_family_avg(all_stats_hawc2, df_input)
    >>> uls_stats = calc_uls(family_stats, all_stats_hawc2)
    >>> uls_stats.ULS
    >>> uls_stats.family_stats is family_stats
    True
    """
    source_family_stats = family_stats
    normalized_family_stats, _ = _normalize_duplicate_columns(
        family_stats, all_stats,
    )
    family_uls = _build_family_uls(normalized_family_stats)
    uls = _build_global_uls(family_uls)
    global_provenance = _build_global_provenance(
        family_uls, normalized_family_stats,
    )

    return ULSStats(
        ULS=uls,
        Family_ULS=family_uls,
        family_stats=source_family_stats,
        global_provenance=global_provenance,
    )
