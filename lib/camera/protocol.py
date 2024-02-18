from lib.rpc.decorators import serializable


@serializable
class ServerProtocol:
    def init(self) -> None:
        ...

    def fini(self) -> None:
        ...

    def start(self, *, test_arg: str) -> str:
        ...


class ProtocolHandler(ServerProtocol):
    metadata = ServerProtocol
