from __future__ import annotations

import socket
from typing import Optional

from .config import WorldStateConfig


class WorldState:
    def __init__(self, sock: socket.socket, address: str):
        self.socket = sock
        self.address = address

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        self.socket.connect(self.address)
        return Connection(self.socket)

    def disconnect(self):
        self.socket.close()

    @classmethod
    def from_config(cls, config: WorldStateConfig) -> WorldState:
        sock = socket.socket(config.socket.family, config.socket.type)
        return cls(sock, config.socket.address)


class Connection:
    def __init__(self, sock: socket.socket):
        self.socket = sock

    def set(self, key: bytes, value: bytes):
        self.socket.send(b' '.join([b'SET', key, value, b'\n']))

    def get(self, key: bytes) -> bytes:
        self.socket.send(b' '.join([b'GET', key, b'\n']))
        buf = self.socket.recv(1024)
        if buf.startswith(b'X'):
            raise KeyError(key)
        return buf[1:]


class Value:
    def __init__(self, path: bytes, typ: type):
        self.path = path
        self.typ = typ

    def __str__(self):
        return self.path.decode()

    def get(self, conn: Connection):
        decoder = {
            int: int,
            float: float,
            bytes: bytes,
            str: bytes.decode,
        }.get(self.typ, lambda x: x)
        return decoder(conn.get(self.path))

    def set(self, conn: Connection, value: bytes):
        encoder = {
            int: lambda x: str(x).encode(),
            float: lambda x: str(x).encode(),
            bytes: bytes,
            str: str.encode,
        }.get(self.typ, lambda x: x)
        conn.set(self.path, encoder(value))


class EntityMeta(type):
    def __new__(mcs, name: str, bases, namespace, **kwargs):
        if name == 'Entity':
            return super().__new__(mcs, name, bases, namespace)

        annotations = namespace.get('__annotations__', {})

        def __init__(self, path: bytes, parent: Optional[Entity] = None):
            Entity.__init__(self, path, parent)

            for attr, typ in annotations.items():
                if isinstance(typ, EntityMeta):
                    setattr(self, attr, typ(attr.encode(), self))
                else:
                    setattr(self, attr, Value(self.path + b'::' + attr.encode(), typ))

        namespace['__init__'] = __init__

        namespace['__str__'] = lambda self: self.path.decode()

        return super().__new__(mcs, name, bases, namespace)


class Entity(metaclass=EntityMeta):
    def __init__(self, path: bytes, parent: Optional[Entity] = None):
        self._path = path
        self.parent = parent

    @property
    def path(self) -> bytes:
        if self.parent:
            return self.parent.path + b'::' + self._path
        return self._path
