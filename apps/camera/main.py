import logging
from lib.camera.protocol import ServerProtocol
from lib.rpc.connection.null import LocalConnection
from lib.rpc.executor import Executor


class Handler(ServerProtocol):
    def start(self, *, test_arg: str) -> str:
        return "Hello World!" + test_arg


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    connection = LocalConnection(handler=Handler())
    executor: ServerProtocol = Executor(protocol=ServerProtocol, connection=connection)
    result = executor.start(test_arg="test")

    print(result)
