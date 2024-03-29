import typing
from dataclasses import dataclass

from .controls import BaseControl
from .protocol import Metadata


@dataclass
class RawFrame:
    sequence: int
    buffer: bytes


class VideoDevice(typing.Protocol):
    async def metadata(self) -> Metadata: ...

    async def start(self, path: str, width: int, height: int): ...

    async def controls(self) -> typing.List[BaseControl]: ...

    async def stop(self): ...

    async def get_frame(self) -> RawFrame: ...


class Encoder(typing.Protocol):
    async def init(self):
        ...

    async def fini(self):
        ...

    async def encode(self, buffer: bytes):
        ...


class Preview(typing.Protocol):
    async def init(self):
        ...

    async def fini(self):
        ...

    async def encode(self, buffer: bytes):
        ...

    async def get_file(self, filename: str):
        ...
