import datetime
import typing

from pydantic import BaseModel

from lib.rpc.decorators import MethodType, _init

T = typing.TypeVar("T")


class CaptureStartData(BaseModel):
    capture_time: datetime.datetime
    index: int

    meta: dict[str, str]


class FrameData(BaseModel):
    index: int
    frame: bytes


class RPCProtocol(typing.Protocol):
    metadata: dict[str, MethodType]

    def __init_subclass__(cls, **kwargs):
        if cls.mro()[1] != __class__:
            return

        cls.metadata = _init(prototype=cls)


def method(func: T) -> T | MethodType:
    setattr(func, "is_proto", True)
    return func


class ServerProtocol(RPCProtocol):
    @method
    async def start(self, *, device_id: int) -> CaptureStartData:
        ...

    @method
    async def stop(self) -> None:
        ...

    @method
    async def iter_frames(self) -> typing.AsyncIterable[FrameData]:
        ...


class CAMProtocol(RPCProtocol):
    @method
    async def call(self) -> typing.AsyncIterable[FrameData]:
        ...


class Test(CAMProtocol):
    pass
