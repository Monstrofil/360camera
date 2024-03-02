import asyncio
import contextlib
from typing import List
from unittest import mock

import pydantic
import pytest

from camera360.lib.rpc.decorators import MethodType
from camera360.lib.rpc.protocol import RPCProtocol, method, RPCHandler
from camera360.lib.rpc.server import start_server, connect


def test_protocol_subclass():
    class DemoProtocol(RPCProtocol):
        @method
        def init(self, arg1: str, arg2: List[str]) -> None:
            pass

        @method
        def finish(self) -> int:
            ...

        def not_a_method(self) -> int:
            ...

    assert DemoProtocol.methods == {
        "init": MethodType(
            args_model=mock.ANY, return_model=mock.ANY),
        "finish": MethodType(
            args_model=mock.ANY, return_model=mock.ANY
        ),
    }

    assert DemoProtocol.methods["init"].args_model(
        arg1="argument1", arg2=["argument2"]
    ).model_dump() == dict(arg1="argument1", arg2=["argument2"])

    assert DemoProtocol.methods["init"].return_model(
        value=None
    ).model_dump() == dict(value=None)

    assert DemoProtocol.methods["finish"].return_model(
        value=123).model_dump() == dict(
            value=123
        )


class DemoProtocol(RPCProtocol):
    demo_response = [1, 3, 5]

    @method
    async def start(self, *, arg1: str, arg2: List[str]) -> list[int]:
        assert arg1 == "argument1"
        assert arg2 == ["argument2"]
        return self.demo_response

    @method
    async def raise_exception(self, arg: str) -> None:
        raise RuntimeError('Something bad happened')

    @method
    async def malformed_return(self) -> int:
        return "invalid string type here"


class DemoHandler(RPCHandler, DemoProtocol):
    def __init__(self):
        super().__init__()


@contextlib.asynccontextmanager
async def background_server(
        server_handler: RPCHandler) -> tuple[str, int]:
    server = await start_server(server_handler, host="127.0.0.1", port=5000)

    host, port = server.sockets[0].getsockname()

    async def server_task():
        async with server:
            await server.serve_forever()

    task = asyncio.create_task(server_task())
    yield host, port
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
    :return:
    """
    server_handler = DemoHandler()
    async with background_server(server_handler=server_handler) as (host, port), \
        connect(host, port, protocol=DemoProtocol) as connection:

            start_result = await connection.start(
                arg1="argument1", arg2=["argument2"])

            assert start_result == DemoHandler.demo_response

            # we don't distinguish errors on server side right now,
            # but we should be able to understand that something is gone wrong
            with pytest.raises(ConnectionError):
                await connection.raise_exception(arg='test')

            # when we pass invalid arguments, we get exception
            # immediately even without attempt to send request
            with pytest.raises(pydantic.ValidationError):
                await connection.start(wrong_argument=123)

            # when handler missed correct response format
            # we should get exception
            with pytest.raises(ConnectionError):
                await connection.malformed_return()
