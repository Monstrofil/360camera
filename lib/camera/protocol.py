import pydantic

from lib.rpc.decorators import serializable


class MethodType:
    args_model: pydantic.BaseModel
    return_model: pydantic.BaseModel


def method(func) -> MethodType:
    return func


@serializable
class ServerProtocol:
    @method
    async def init(self) -> int:
        ...

    @method
    async def fini(self) -> None:
        ...

    @method
    async def start(self, *, test_arg: str) -> str:
        ...
