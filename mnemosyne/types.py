
from dataclasses import dataclass, field

class Remote:
    @staticmethod
    def parse(remote):

        if remote["type"] == "cifs":
            return CifsRemote(**remote)

        raise RuntimeError("Don't know remote type '" + remote["type"] + "'")

@dataclass
class CifsRemote:
    type: str
    volume: str
    username: str
    password: str

@dataclass
class Store:
    name: str
    size: int
    keyfile: str

@dataclass
class Strategy:
    stages: int
    rotate: int

@dataclass
class Directory:
    key: int
    directory: int

@dataclass
class Local:
    directories: list[Directory]
