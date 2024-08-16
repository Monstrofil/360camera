import enum
from typing import List, Optional, Any

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

    clients: List[Client] = pydantic.Field(default_factory=list)


class SupervisorProtocol(RPCProtocol):
    @method
    async def get_clients(self) -> List[Client]: ...

    @method
    async def captures(self) -> list: ...

    @method
    async def start(self) -> None: ...

    @method
    async def stop(self) -> None: ...

    @method
    async def controls(self) -> list[AnyControl]: ...

    @method
    async def camera_controls(self) -> dict[str, list[AnyControl]]:
        ...

    @method
    async def set_controls(self, *, values: dict[str, Any]) -> None:
        ...

    @method
    async def set_camera_control(self, *, camera_id: str, name: str, value: Any) -> None:
        ...

    @method
    async def status(self) -> Status: ...

    @method
    async def events(self) -> None: ...

    @method
    async def preview(self, *, camera_id: str) -> bytes: ...
