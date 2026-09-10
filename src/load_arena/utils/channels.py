"""Shared validation for explicitly selected simulation channels."""

import pandas as pd
from typing import Literal


ChannelSelection = list[str] | Literal["all"]


def validate_channels(channels: object) -> list[str]:
    """Validate a nonempty, ordered list of unique channel names.

    Parameters
    ----------
    channels : object
        Requested channel names.

    Returns
    -------
    list[str]
        Validated names with their spelling and order preserved.

    Examples
    --------
    >>> validate_channels(["Load_[kN]"])
    ['Load_[kN]']
    """
    if not isinstance(channels, list) or not channels:
        raise ValueError("channels must be a nonempty list of channel names.")
    if any(not isinstance(name, str) or not name.strip() for name in channels):
        raise ValueError("channels must contain nonblank strings.")
    if len(set(channels)) != len(channels):
        raise ValueError("channels must be unique.")
    return channels


def select_channels(data: pd.DataFrame, channels: ChannelSelection, context: str) -> pd.DataFrame:
    """Select requested channels, rejecting missing names in a simulation.

    Parameters
    ----------
    data : pandas.DataFrame
        Simulation samples with reader-generated column names.
    channels : list[str] or {"all"}
        Validated channel selection, or every channel in simulation order.
    context : str
        Analysis and simulation identity for errors.

    Returns
    -------
    pandas.DataFrame
        Samples restricted to selected channels.

    Examples
    --------
    >>> select_channels(pd.DataFrame({"load": [1]}), ["load"], "case.int").shape
    (1, 1)
    """
    if channels == "all":
        channels = validate_channels(data.columns.tolist())
    missing = [name for name in channels if name not in data.columns]
    if missing:
        raise ValueError(f"{context}: requested channels not found: {missing}")
    return data.loc[:, channels]
