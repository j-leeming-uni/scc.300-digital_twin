from typing import Optional, Literal

from .config import Config

Direction = Literal['north', 'east', 'south', 'west']

NEIGHBOURS: dict[Direction, Optional[int]] = {
    'north': None,
    'east': None,
    'south': None,
    'west': None,
}


def init(cfg: Config):
    global NEIGHBOURS
    if cfg.junction_id == 1:
        NEIGHBOURS['east'] = 2
    elif cfg.junction_id == 2:
        NEIGHBOURS['west'] = 1
