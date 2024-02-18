from lib.rpc.decorators import serializable


@serializable
class ServerProtocol:
    async def init(self) -> None:
        ...

    async def fini(self) -> None:
        ...

    async def start(self, *, test_arg: str) -> str:
        ...

