import asyncio
import logging
import traceback
from typing import Optional

import pydantic
from pydantic import BaseModel

from camera360.lib.rpc.connection import MethodCall, MethodReturn
from camera360.lib.rpc.protocol import RPCHandler


class Message(BaseModel):
    payload: bytes

    request_id: Optional[int] = None
    response_id: Optional[int] = None


class Iterator:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def put(self, item):
        await self.queue.put(item)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self.queue.get()
        if isinstance(item, Exception):
            raise item
        return item


class Channel:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        handler: Optional[RPCHandler],
    ):
        self.reader = reader
        self.writer = writer
        self.handler = handler

        # todo: rename to is_connected or somthing like that
        self._is_dead = False

        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}

    def on_loop_done(self, future: asyncio.Future):
        print('done')

    async def __aenter__(self):
        self._loop = asyncio.create_task(self._receive_messages_loop())
        self._loop.add_done_callback(self.on_loop_done)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._loop.cancel()

        try:
            await self._loop
        except asyncio.CancelledError:
            pass

    async def serve_forever(self):
        await self._receive_messages_loop()

    async def _receive_messages_loop(self):
        while True:
            logging.info('Starting loop for channel %s', self)
            try:
                raw_message = await self.reader.readline()
            except ConnectionResetError:
                logging.warning('Client disconnected')
                break

            # windows machines return empty strings when peer is offline
            # we don't really care about the reason why somebody
            # disconnected here, so just break the loop
            if raw_message == b"":
                break

            logging.info('Message received in channel %s', self)
            try:
                await self.data_received(raw_message)
            except Exception as e:
                traceback.print_exception(e)

        self._is_dead = True
        for future in self._pending_requests.values():
            future.set_exception(ConnectionResetError("Channel connection lost"))

    async def send_request(self, payload: bytes) -> Iterator | bytes:
        if self._is_dead:
            raise ConnectionResetError("Dead channel")

        request = Message(request_id=self._request_id, payload=payload)
        self._pending_requests[request.request_id] = future = asyncio.Future()
        self._request_id += 1

        self.writer.write(request.model_dump_json().encode() + b"\n")

        return await future

    async def send_response(self, request_id: int, payload: bytes) -> None:
        self.writer.write(
            Message(response_id=request_id, payload=payload).model_dump_json().encode()
            + b"\n"
        )
        await self.writer.drain()

    async def _is_response_unbound(self, message: Message):
        return await self._is_response(message) \
            and message.response_id not in self._pending_requests

    async def _is_response(self, message: Message) -> bool:
        return bool(message.response_id is not None)

    async def data_received(self, raw_message: bytes) -> None:
        message = Message.model_validate_json(raw_message)

        if await self._is_response_unbound(message):
            logging.warning("Response id {} not expected".format(message.request_id))
            return

        if await self._is_response(message):
            await self._response_received(message)
        else:
            logging.info("Got request with id {}".format(message.request_id))

            tcp_data = MethodCall.model_validate_json(message.payload)

            # getting metadata of the methods to be able to unpack payload
            if self.handler is None:
                return

            method_meta = self.handler.methods[tcp_data.method]
            arguments = method_meta.args_model.model_validate_json(tcp_data.arguments)

            # actually executing what we have in handler
            try:
                callable = getattr(self.handler, tcp_data.method)
                response = await callable(**arguments.model_dump())
            except:
                traceback.print_exc()
                await self.send_response(
                    message.request_id,
                    MethodReturn(value=b'', type="exception")
                    .model_dump_json()
                    .encode(),
                )
                return

            try:
                response_raw = (
                    method_meta.return_model(value=response)
                    .model_dump_json()
                    .encode()
                )
            except pydantic.ValidationError as e:
                logging.error('Method %s returned invalid response type: %s',
                              tcp_data.method, e)
                return await self.send_response(
                    message.request_id,
                    MethodReturn(value=b'', type="exception")
                    .model_dump_json()
                    .encode()
                )

            logging.info(
                "Request id={} response={}".format(
                    message.request_id, response_raw[:50])
            )

            await self.send_response(
                message.request_id,
                MethodReturn(value=response_raw, type="return")
                .model_dump_json()
                .encode(),
            )

    async def _response_received(self, message: Message):
        rpc_response = MethodReturn.model_validate_json(message.payload)

        if rpc_response.type == 'exception':
            self._pending_requests.pop(
                message.response_id
            ).set_exception(ConnectionError())
        else:
            self._pending_requests.pop(
                message.response_id
            ).set_result(
                rpc_response.value
            )
