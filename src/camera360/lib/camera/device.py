import typing
from dataclasses import dataclass

from .controls import BaseControl
from .protocol import Metadata
from camera360.lib.supervisor.protocol import FrameData


@dataclass
class RawFrame:
    sequence: int
    buffer: bytes


class API(typing.Protocol):
    async def metadata(self) -> Metadata:
        ...

    async def start(self, path: str, width: int, height: int):
        ...

    async def controls(self) -> typing.List[BaseControl]:
        ...

    async def stop(self):
        ...

    async def get_frame(self) -> RawFrame:
        ...
