import dataclasses
from pathlib import Path


@dataclass
class LoadArenaConfig:
    """ 
    coniguration for loading data and different parameters name

    """

    def __init__(self, sims_path: str | Path) -> None:
        self.sims_path: str | Path =  sims_path

        
