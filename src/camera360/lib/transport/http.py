import contextlib
import logging
import typing
from functools import partial

import aiohttp
import fastapi
import uvicorn

from ..rpc.decorators import MethodType
from ..rpc.protocol import RPCHandler, RPCProtocol


def start_server(handler: RPCHandler, host: str = "127.0.0.1", port: int = 8000, lifespan = None):

    app = fastapi.FastAPI(lifespan=lifespan)
    for method in handler.methods:
        app.add_api_route(f'/{method}', endpoint=getattr(handler, method), methods=["POST"])

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
        print(kwargs)
        response = await self._session.request("POST", f"/{method_name}", params=kwargs)

        json_text = await response.json()
        return method.return_model(value=json_text).value



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
