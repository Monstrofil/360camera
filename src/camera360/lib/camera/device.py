import typing
from dataclasses import dataclass

from .controls import AnyControl
from .protocol import Metadata


@dataclass
class RawFrame:
    width: int
    height: int
    sequence: int
    buffer: bytes


class TimeoutError(OSError):
    ...

class VideoDevice(typing.Protocol):
    def __init__(self, media_path: str) -> None:
        super().__init__()

    async def metadata(self) -> Metadata: ...

    async def start(self, width: int, height: int): ...

    async def controls(self) -> typing.List[AnyControl]: ...

    async def set_control(self, control_name: str, value: int) -> None: ...

    async def stop(self): ...

    async def get_frame(self, frames: int | None = None) -> typing.AsyncIterable[RawFrame]: ...


class Encoder(typing.Protocol):
    async def init(self, width: int, height: int) -> None:
        ...

    async def fini(self):
        ...

    async def encode(self, frame: RawFrame):
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


class Factory(typing.Protocol):
    async def list_devices(self) -> list[VideoDevice]: ...
