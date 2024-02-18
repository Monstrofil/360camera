import datetime

import pydantic
from pydantic import BaseModel

from lib.rpc.decorators import serializable


class MethodType:
    args_model: pydantic.BaseModel
    return_model: pydantic.BaseModel


def method(func) -> MethodType:
    return func


class CaptureStartData(BaseModel):
    capture_time: datetime.datetime
    index: int

    meta: dict[str, str]


@serializable
class ServerProtocol:
    @method
    async def init(self) -> int:
        ...

    @method
    async def fini(self) -> None:
        ...

    @method
    async def start(self, *, test_arg: str) -> CaptureStartData:
        ...
