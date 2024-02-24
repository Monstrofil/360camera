import datetime

from pydantic import BaseModel

from lib.rpc.protocol import RPCProtocol, method


class CaptureStartData(BaseModel):
    capture_time: datetime.datetime
    index: int

    meta: dict[str, str]


class Mode(BaseModel):
    width: int
    height: int

    bpp: int


class Metadata(BaseModel):
    name: str
    modes: list[Mode]


class CameraProtocol(RPCProtocol):
    @method
    async def metadata(self) -> Metadata:
        ...

    @method
    async def start(
        self, *, device_id: int, width: int, height: int
    ) -> CaptureStartData:
        ...

    @method
    async def stop(self) -> None:
        ...
