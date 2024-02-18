import datetime
from typing import Generator

import pydantic
from pydantic import BaseModel

from lib.rpc.decorators import serializable


class MethodType:
    args_model: pydantic.BaseModel
    return_model: pydantic.BaseModel
    method_type: str


def method(func) -> MethodType:
    return func


class CaptureStartData(BaseModel):
    capture_time: datetime.datetime
    index: int

    meta: dict[str, str]


class FrameData(BaseModel):
    index: int


@serializable
class ServerProtocol:
    # todo: search for the ways to eliminate this line
    #   right now pycharm is seriously confused about
    #   types without this hack
    metadata: "ServerProtocol"

    @method
    async def start(self, *, device_id: int) -> CaptureStartData:
        ...

    @method
    async def stop(self) -> None:
        ...

    @method
    async def iter_frames(self) -> Generator[FrameData, None, None]:
        ...
