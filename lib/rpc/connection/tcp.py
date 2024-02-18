import asyncio
import logging

from pydantic import BaseModel

from lib.rpc.connection import Connection


class TcpPayload(BaseModel):
    method: str
    arguments: bytes

    type: str = "method_call"


class TcpConnection(Connection, asyncio.Protocol):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__()
        self.reader = reader
        self.writer = writer

    async def communicate(self, method_name: str, arguments: bytes):
        logging.info("Sending request %s", arguments)
        tcp_payload = TcpPayload(arguments=arguments, method=method_name)
        self.writer.write(tcp_payload.json().encode() + b"\n")

        response = await self.reader.readline()
        logging.info("Got response %s", response)

        return response

    async def receive_message(self, method_name: str, arguments: bytes):
        mathod = getattr(self._handler, method_name)
        method_meta = getattr(self._handler.metadata, method_name)

        arguments = method_meta.model.parse_raw(arguments)
        return mathod(**arguments.dict())
