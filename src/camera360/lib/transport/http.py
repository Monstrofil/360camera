import contextlib
import functools
import logging
import typing
from functools import partial

import aiohttp
import fastapi
import uvicorn

from ..rpc.decorators import MethodType
from ..rpc.protocol import RPCHandler, RPCProtocol


def start_server(handler: RPCHandler, host: str = "127.0.0.1", port: int = 8000, lifespan=None):
    app = fastapi.FastAPI(lifespan=lifespan)
    for method_name, method_data in handler.methods.items():
        def create_route_handler(function: typing.Callable[..., typing.Coroutine]):
            async def method_proxy(arguments: method_data.args_model = fastapi.Body(...)):
                try:
                    response = await function(**dict(arguments))
                    logging.info('%s %s', response, type(response))
                except Exception as e:
                    raise fastapi.HTTPException(status_code=404, detail=str(e))
                return {
                    "value": response
                }

            return method_proxy

        method_data.__name__ = getattr(handler, method_name).__name__
        method_data.__qualname__ = getattr(handler, method_name).__qualname__
        method_data.__doc__ = getattr(handler, method_name).__doc__

        app.add_api_route(f'/{method_name}',
                          endpoint=create_route_handler(getattr(handler, method_name)),
                          methods=["POST"],
                          response_model=method_data.return_model)

    uvicorn.run(app, host=host, port=port)


T = typing.TypeVar("T")


@contextlib.asynccontextmanager
async def connect(
        host: str, port: int, protocol: type[T], handler=None
) -> typing.AsyncContextManager[T]:
    conn = Connection(host, port)
    executor = await conn.connect(protocol, handler)

    yield executor


T = typing.TypeVar("T")


class HttpExecutor(typing.Generic[T]):
    def __init__(self, protocol: T, session: aiohttp.ClientSession):
        self._protocol: RPCProtocol = protocol
        self._session = session

        for name, member in self._protocol.methods.items():
            logging.debug("Processing method %s", member)

            # copying methods from the protocol but overriding them with remote call logic
            self.__dict__[name] = partial(self._call_remote_method, member, name)

    def __repr__(self):
        return f"RemotePython[{self._protocol.__name__}] at {hex(id(self))}"

    async def _call_remote_method(self, method: MethodType, method_name, **kwargs) -> T:
        response = await self._session.request("POST", f"/{method_name}", json=kwargs)

        if response.status == 200:
            json_text = await response.json()
            return method.return_model(**json_text).value

        else:
            raise Exception(await response.json())


class Connection:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def connect(
            self,
            protocol: type[T],
            handler: typing.Optional[RPCHandler]) -> T:
        logging.info("Connection to the server established")

        session = aiohttp.ClientSession(base_url=f'http://{self.host}:{self.port}')
        executor: T = HttpExecutor(protocol=protocol, session=session)

        return executor

    async def wait_for_disconnect(self):
        ...

    async def disconnect(self):
        ...

    async def on_lost_connection(self):
        ...
