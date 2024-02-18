import asyncio
import logging
from typing import AsyncIterator

from . import Connection, RPCRequest, RPCResponse


class TcpConnection(Connection, asyncio.Protocol):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__()
        self.reader = reader
        self.writer = writer

    async def communicate(self, method_name: str, arguments: bytes) -> RPCResponse:
        logging.info("Sending request %s", arguments)
        tcp_payload = RPCRequest(arguments=arguments, method=method_name)
        self.writer.write(tcp_payload.model_dump_json().encode() + b"\n")

        response = await self.reader.readline()
        logging.info("Got response %s", response)

        return RPCResponse.parse_raw(response)

    async def stream(
        self, method_name: str, arguments: bytes
    ) -> AsyncIterator[RPCResponse]:
        logging.info("Sending request %s", arguments)
        tcp_payload = RPCRequest(arguments=arguments, method=method_name)
        self.writer.write(tcp_payload.model_dump_json().encode() + b"\n")

        while True:
            response = await self.reader.readline()
            logging.info("Got yield %s", response)

            rpc_response = RPCResponse.parse_raw(response)
            if rpc_response.type == "stop_iteration":
                return

            yield rpc_response

    async def receive_message(self, method_name: str, arguments: bytes):
        mathod = getattr(self._handler, method_name)
        method_meta = getattr(self._handler.metadata, method_name)

        arguments = method_meta.model.parse_raw(arguments)
        return mathod(**arguments.dict())
