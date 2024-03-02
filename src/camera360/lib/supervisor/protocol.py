import enum
from typing import List, Optional

import pydantic
from pydantic import BaseModel

from ..camera.controls import AnyControl
from ..rpc.protocol import RPCProtocol, method


class FrameData(BaseModel):
    index: int


class Client(BaseModel):
    name: str


class SystemStatus(enum.Enum):
    idle = "idle"
    capture = "capture"


class Status(BaseModel):
    status: SystemStatus = SystemStatus.idle
    pending_status: Optional[SystemStatus] = None

    clients: List[Client] = pydantic.Field(
        default_factory=list)



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

    @method
    async def status(self) -> Status:
        ...

    @method
    async def events(self) -> None:
        ...

    @method
    async def preview(self, *, filename: str) -> bytes:
        ...
