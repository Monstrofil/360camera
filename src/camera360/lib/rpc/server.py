import asyncio
import contextlib
import logging
import typing

from .connection.channel import Channel
from .executor import RemotePython
from .protocol import RPCHandler
from ..camera.protocol import CameraProtocol
from ..supervisor.protocol import SupervisorProtocol


async def start_server(handler: RPCHandler, host: str = "127.0.0.1", port: int = 8000):
    async def create_channel(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer = writer.transport.get_extra_info("peername")
        logging.info("Creating channel %s", peer)

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
    host: str, port: int, protocol: type[T], handler=None
) -> typing.AsyncContextManager[T]:
    conn = Connection(host, port)
    executor = await conn.connect(protocol, handler)

    async with conn.channel:
        yield executor


class Connection:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.channel = None

    async def connect(
            self,
            protocol: type[T],
            handler: typing.Optional[RPCHandler]) -> T:
        reader, writer = await asyncio.open_connection(
            host=self.host, port=self.port, limit=10 * 1024 * 1024
        )
        logging.info("Connection to the server established")

        self.channel = Channel(reader, writer, handler=handler)
        executor: T = RemotePython(protocol=protocol, channel=self.channel)

        await self.channel.start(on_lost_connection_cb=self.on_lost_connection)

        return executor

    async def wait_for_disconnect(self):
        if self.channel is None:
            raise ValueError("No connection to server")

        await self.channel.on_disconnect_event.wait()

    async def disconnect(self):
        await self.channel.close()

    async def on_lost_connection(self):
        ...
