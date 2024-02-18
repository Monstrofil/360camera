import asyncio
import functools
import logging
import types

import typer

from lib.camera.protocol import ServerProtocol
from lib.rpc.connection.tcp import TcpConnection
from lib.rpc.executor import Executor


class Application(ServerProtocol):
    def __init__(self):
        self.cli = typer.Typer()
        # register all known methods as cli commands
        for name, method in self.registered.items():
            self.cli.command()(self._create_command_callback(name, getattr(self, name)))

    async def run_command(self, name, *args, **kwargs):
        reader, writer = await asyncio.open_connection(host="127.0.0.1", port=8000)
        logging.info("Connection to the server established")

        connection = TcpConnection(reader, writer)
        executor: ServerProtocol = Executor(
            protocol=ServerProtocol, connection=connection
        )

        async_method = getattr(executor, name)(*args, **kwargs)
        method_result = await async_method

        if isinstance(method_result, types.AsyncGeneratorType):
            while True:
                try:
                    item = await method_result.__anext__()
                except StopAsyncIteration:
                    break
                print(item)
        else:
            print("result", method_result.dict())

        writer.close()
        await writer.wait_closed()

    def _create_command_callback(self, name, future):
        @functools.wraps(future)
        def call_command_wrapper(*args, **kwargs):
            logging.info("Got a call with arguments %s %s %s", name, args, kwargs)

            result = asyncio.run(self.run_command(name, *args, **kwargs))
            if isinstance(result, types.GeneratorType):
                for item in result:
                    print(item)
            else:
                print(result)

        return call_command_wrapper

    def run(self):
        self.cli()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    main()
