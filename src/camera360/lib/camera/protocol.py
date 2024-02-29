import datetime

from pydantic import BaseModel

from camera360.lib.rpc.protocol import RPCProtocol, method


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
    async def metadata(self) -> Metadata:
        ...

    @method
    async def start(
        self, *, device_path: str, width: int, height: int
    ) -> CaptureStartData:
        ...

    @method
    async def controls(self):
        ...

    @method
    async def stop(self) -> None:
        ...

    @method
    async def reset(self) -> None:
        ...
