from __future__ import annotations

import socket
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def load(path: str | Path):
    path = Path(path)
    with path.open('rb') as f:
        raw_config = tomllib.load(f)
    return Config.parse(raw_config)


@dataclass
class Config:
    world_state: WorldStateConfig
    junctions: dict[int, JunctionConfig]
    protections: Protections
    junction_id: Optional[int] = None

    @classmethod
    def parse(cls, raw_config: dict) -> Config:
        return cls(
            world_state=WorldStateConfig.parse(raw_config['world_state']),
            junctions={j.id: j for j in JunctionConfig.parse_all(raw_config['junction'])},
            protections=Protections.parse(raw_config.get('protections', {})),
            junction_id=raw_config.get('junction_id'),
        )


@dataclass
class WorldStateConfig:
    socket: SocketConfig

    @classmethod
    def parse(cls, raw_config: dict) -> WorldStateConfig:
        return cls(socket=SocketConfig.parse(raw_config))


class SocketConfig(ABC):
    @property
    @abstractmethod
    def address(self):
        pass

    @property
    @abstractmethod
    def family(self):
        pass

    @property
    def type(self):
        return socket.SOCK_STREAM

    @classmethod
    def parse(cls, raw_config: dict) -> SocketConfig:
        if 'socket' in raw_config:
            return DomainSocketConfig.parse(raw_config)
        raise ValueError(f"Unknown socket type: {raw_config}")


@dataclass
class DomainSocketConfig(SocketConfig):
    path: str

    @property
    def address(self):
        return self.path

    @property
    def family(self) -> socket.AddressFamily:
        return socket.AF_UNIX

    @classmethod
    def parse(cls, raw_config: dict) -> DomainSocketConfig:
        return cls(path=raw_config['socket'])


@dataclass
class JunctionConfig:
    id: int
    socket: SocketConfig
    neighbours: dict[str, int]

    @classmethod
    def parse(cls, raw_config: dict) -> JunctionConfig:
        return cls(
            id=raw_config['id'],
            socket=SocketConfig.parse(raw_config),
            neighbours=raw_config['neighbours'],
        )

    @classmethod
    def parse_all(cls, raw_config: dict) -> list[JunctionConfig]:
        return [cls.parse(j) for j in raw_config]


@dataclass
class Protections:
    dos: bool = False
    repudiation: bool = False

    @classmethod
    def parse(cls, raw_config: dict[str, bool]) -> Protections:
        return cls(
            dos=raw_config.get('dos', False),
            repudiation=raw_config.get('repudiation', False),
        )
