import dataclasses
import pathlib as path


@dataclass
class LoadArenaConfig:
    """
    coniguration for loading data and different parameters name

    """

    def __init__(self):
        self.res_path = None
