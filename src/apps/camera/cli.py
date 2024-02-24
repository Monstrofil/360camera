import asyncio
import functools
import logging
import types

import typer

from lib.camera.protocol import CameraProtocol
from lib.rpc.server import connect


class Application(CameraProtocol):
    def __init__(self):
        self.cli = typer.Typer()
        # register all known methods as cli commands
        for name, method in self.methods.items():
            self.cli.command()(self._create_command_callback(name, getattr(self, name)))

    async def run_command(self, name, *args, **kwargs):
        executor = await connect(host="127.0.0.1", port=8000, protocol=CameraProtocol)

        async_method = getattr(executor, name)(*args, **kwargs)
        method_result = await async_method

        if isinstance(method_result, types.AsyncGeneratorType):
            while True:
                try:
                    item = await method_result.__anext__()
                except StopAsyncIteration:
                    break
                print(item)
        elif method_result is None:
            return
        else:
            print("result", method_result.dict())

    def _create_command_callback(self, name, future):
        @functools.wraps(future)
        def call_command_wrapper(*args, **kwargs):
            logging.info("Got a call with arguments %s %s %s", name, args, kwargs)

            asyncio.run(self.run_command(name, *args, **kwargs))

        return call_command_wrapper

    def run(self):
        self.cli()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    main()
