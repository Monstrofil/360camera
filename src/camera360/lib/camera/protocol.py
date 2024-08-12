import datetime
import typing

from pydantic import BaseModel

from camera360.lib.rpc.protocol import RPCProtocol, method
from camera360.lib.camera.controls import NumericControl, AnyControl


class CaptureStartData(BaseModel):
    capture_time: datetime.datetime
    index: int

    meta: dict[str, str]


class Mode(BaseModel):
    width: int
    height: int

    bpp: int


class Camera(BaseModel):
    name: str
    path: str
    modes: list[Mode]


class Metadata(BaseModel):
    devices: list[Camera]


class CameraProtocol(RPCProtocol):
    @method
    async def id(self) -> str: ...

    @method
    async def devices(self) -> list[str]: ...

    @method
    async def metadata(self) -> Metadata: ...

    @method
    async def start(
        self, *, device_path: str, width: int, height: int
    ) -> CaptureStartData: ...

    @method
    async def controls(self, *, device_path: str) -> list[AnyControl]: ...

    @method
    async def set_control(self, *, device_path: str, control_name: str, value: int):
        ...

    @method
    async def stop(self, *, device_path: str) -> None: ...

    @method
    async def reset(self, *, device_path: str) -> None: ...

    @method
    async def preview(self, *, device_path: str) -> bytes: ...
