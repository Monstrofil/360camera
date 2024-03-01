from typing import List

from pydantic import BaseModel

from ..camera.controls import BaseControl, AnyControl
from ..rpc.protocol import RPCProtocol, method


class FrameData(BaseModel):
    index: int
    frame: bytes


class Client(BaseModel):
    name: str


class SupervisorProtocol(RPCProtocol):
    @method
    async def on_frame_received(self, *, frame: FrameData) -> None:
        ...

    @method
    async def get_clients(self) -> List[Client]:
        ...

    @method
    async def start(self) -> None:
        ...

    @method
    async def stop(self) -> None:
        ...

    @method
    async def controls(self) -> List[AnyControl]:
        ...
