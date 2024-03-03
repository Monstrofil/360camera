import asyncio
import contextlib
import logging
from typing import List

import pydantic
import pytest

from camera360.lib.rpc.protocol import RPCProtocol, method, RPCHandler
from camera360.lib.rpc.server import start_server, connect


class DemoProtocol(RPCProtocol):
    demo_response = [1, 3, 5]

    @method
    async def start(self, *, arg1: str, arg2: List[str]) -> list[int]:
        assert arg1 == "argument1"
        assert arg2 == ["argument2"]
        return self.demo_response

    @method
    async def raise_exception(self, arg: str) -> None:
        raise RuntimeError("Something bad happened")

    @method
    async def malformed_return(self) -> int:
        return "invalid string type here"

    @method
    async def long_waiting_method(self) -> int:
        await asyncio.sleep(5)
        return 1


class DemoHandler(RPCHandler, DemoProtocol):
    def __init__(self):
        super().__init__()
        self.clients = []

    async def on_client_connected(self, client):
        logging.info("Client connected")
        self.clients.append(client)

    async def on_client_disconnected(self, client):
        logging.info("Client Disconnected")
        self.clients.remove(client)


@contextlib.asynccontextmanager
async def background_server(server_handler: RPCHandler) -> tuple[str, int]:
    server = await start_server(server_handler, host="127.0.0.1", port=5000)

    host, port = server.sockets[0].getsockname()

    async def server_task():
        async with server:
            await server.serve_forever()

    task = asyncio.create_task(server_task())
    try:
        yield host, port
    finally:
        logging.info("Stopping server")
        server.close()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_connect_and_communicate():
    """
    Generic case when we try to connect to the server
    and communicate with it getting either errors or
    successful responses.
    """
    server_handler = DemoHandler()
    async with (
        background_server(server_handler=server_handler) as (host, port),
        connect(host, port, protocol=DemoProtocol) as connection,
    ):
        # generic call and response should be as expected
        start_result = await connection.start(arg1="argument1", arg2=["argument2"])
        assert start_result == DemoHandler.demo_response

        # we don't distinguish errors on server side right now,
        # but we should be able to understand that something is gone wrong
        with pytest.raises(ConnectionError):
            await connection.raise_exception(arg="test")

        # when we pass invalid arguments, we get exception
        # immediately even without attempt to send request
        with pytest.raises(pydantic.ValidationError):
            await connection.start(wrong_argument=123)

        # when handler missed correct response format
        # we should get exception
        with pytest.raises(ConnectionError):
            await connection.malformed_return()


@pytest.mark.asyncio
async def test_connection_client_disconnects():
    """
    Generic case when we try to connect to the server
    and communicate with it getting either errors or
    successful responses.
    """
    server_handler = DemoHandler()
    async with (
        background_server(server_handler=server_handler) as (host, port),
    ):
        async with connect(host, port, protocol=DemoProtocol) as connection:
            task = asyncio.create_task(connection.long_waiting_method())

            await asyncio.sleep(0.2)

            assert len(server_handler.clients) == 1

        with pytest.raises(ConnectionResetError):
            await task

        # add a little time for the server to detect missing client
        await asyncio.sleep(0.1)
        logging.info("Checking")
        assert len(server_handler.clients) == 0
