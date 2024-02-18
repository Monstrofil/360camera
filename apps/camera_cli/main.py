import asyncio
import functools
import logging

import typer

from lib.camera.protocol import ServerProtocol
from lib.rpc.connection.tcp import TcpConnection
from lib.rpc.executor import Executor

# file: root/__init__.py
from functools import wraps
from asyncio import run


# This is a standard decorator that takes arguments
# the same way app.command does but with
# app as the first parameter
def async_command(app, *args, **kwargs):
    def decorator(async_func):
        # Now we make a function that turns the async
        # function into a synchronous function.
        # By wrapping async_func we preserve the
        # meta characteristics typer needs to create
        # a good interface, such as the description and
        # argument type hints
        @wraps(async_func)
        def sync_func(*_args, **_kwargs):
            return run(async_func(*_args, **_kwargs))

        # Now use app.command as normal to register the
        # synchronous function
        app.command(*args, **kwargs)(sync_func)

        # We return the async function unmodifed,
        # so its library functionality is preserved
        return async_func

    return decorator


# as a method injection, app will be replaced as self
# making the syntax exactly the same as it used to be.
# put this all in __init__.py and it will be injected into
# the library project wide
typer.Typer.async_command = async_command


class Application(ServerProtocol):
    def __init__(self):
        self.cli = typer.Typer()
        # register all known methods as cli commands
        for name, method in self.registered.items():
            self.cli.command()(self._create_command_callback(name, getattr(self, name)))

    async def run_command(self, name, *args, **kwargs):
        reader, writer = await asyncio.open_connection(host="127.0.0.1", port=8000)
        connection = TcpConnection(reader, writer)
        executor: ServerProtocol = Executor(
            protocol=ServerProtocol, connection=connection
        )

        async_method = getattr(executor, name)
        result = await async_method(*args, **kwargs)

        writer.close()
        await writer.wait_closed()

        return result

    def _create_command_callback(self, name, future):
        @functools.wraps(future)
        def call_command_wrapper(*args, **kwargs):
            logging.info("Got a call with arguments %s %s %s", name, args, kwargs)

            result = asyncio.run(self.run_command(name, *args, **kwargs))
            print(result)

        return call_command_wrapper

    def run(self):
        self.cli()


def main():
    logging.info("Connnection to the server established")

    app = Application()
    app.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    main()
