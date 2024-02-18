import asyncio
import logging
from typing import Generator

from . import Connection, RPCRequest, RPCResponse


class TcpConnection(Connection, asyncio.Protocol):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__()
        self.reader = reader
        self.writer = writer

    async def stream(
        self, method_name: str, arguments: bytes
    ) -> RPCResponse | Generator[RPCResponse, None, None]:
        logging.info("Sending request %s", arguments)

        tcp_payload = RPCRequest(arguments=arguments, method=method_name)
        self.writer.write(tcp_payload.model_dump_json().encode() + b"\n")

        async def loop():
            while True:
                response = await self.reader.readline()
                logging.info("Got yield %s", response)

                rpc_response = RPCResponse.parse_raw(response)
                if rpc_response.type == "stop_iteration":
                    return

                if rpc_response.type == "error":
                    raise RuntimeError(rpc_response.value)

                yield rpc_response

        return (item async for item in loop())

    async def receive_message(self, method_name: str, arguments: bytes):
        mathod = getattr(self._handler, method_name)
        method_meta = getattr(self._handler.metadata, method_name)

        arguments = method_meta.model.parse_raw(arguments)
        return mathod(**arguments.dict())
