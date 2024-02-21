import asyncio
import logging
import typing

from .connection.channel import Channel
from .executor import Executor
from ..camera.protocol import ServerProtocol


async def start_server(handler, host: str = "127.0.0.1", port: int = 8000):
    _channels: dict[tuple[str, int], Channel] = dict()

    async def create_channel(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer = writer.transport.get_extra_info("peername")

        if peer in _channels:
            raise RuntimeError("Channel already exists")

        _channels[peer] = Channel(reader, writer, handler)

    server = await asyncio.start_server(
        host=host, port=port, client_connected_cb=create_channel
    )

    async with server:
        await server.serve_forever()


T = typing.TypeVar("T")


async def connect(host: str, port: int, protocol: type[T]) -> T:
    reader, writer = await asyncio.open_connection(host=host, port=port)
    logging.info("Connection to the server established")

    channel = Channel(reader, writer, handler=None)
    executor: ServerProtocol = Executor(protocol=protocol, channel=channel)

    return executor
