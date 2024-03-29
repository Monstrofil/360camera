import typing

from .decorators import MethodType, _init


class RPCHandler:
    def __init__(self): ...

    async def on_client_connected(self, client): ...

    async def on_client_disconnected(self, client): ...


class RPCProtocol(typing.Protocol):
    methods: dict[str, MethodType]

    def __init_subclass__(cls, **kwargs):
        if cls.mro()[1] != __class__:
            return

        cls.methods = _init(prototype=cls)


T = typing.TypeVar("T")


def method(func: T) -> T | MethodType:
    setattr(func, "is_proto", True)
    return func
