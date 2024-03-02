import asyncio
import contextlib
import logging
import typing

from .connection.channel import Channel
from .executor import RemotePython
from .protocol import RPCHandler
from ..camera.protocol import CameraProtocol
from ..supervisor.protocol import SupervisorProtocol


async def start_server(
        handler: RPCHandler,
        host: str = "127.0.0.1",
        port: int = 8000):
    async def create_channel(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer = writer.transport.get_extra_info("peername")
        logging.info('Creating channel %s', peer)

        channel = Channel(reader, writer, handler)

        remote: SupervisorProtocol = RemotePython(
            protocol=SupervisorProtocol, channel=channel
        )
        await handler.on_client_connected(remote)
        await channel.serve_forever()
        await handler.on_client_disconnected(remote)

    server = await asyncio.start_server(
        host=host, port=port, client_connected_cb=create_channel
    )

    return server


T = typing.TypeVar("T")


@contextlib.asynccontextmanager
async def connect(
        host: str, port: int,
        protocol: type[T], handler=None) -> typing.AsyncContextManager[T]:
    reader, writer = await asyncio.open_connection(
        host=host, port=port, limit=10 * 1024 * 1024)
    logging.info("Connection to the server established")

    channel = Channel(reader, writer, handler=handler)
    executor: CameraProtocol = RemotePython(protocol=protocol, channel=channel)

    async with channel:
        yield executor
