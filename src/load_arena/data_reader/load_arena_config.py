from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoadArenaConfig:
    """
    coniguration for loading data and different parameters name

    """

    sims_path: str | Path
