import asyncio
import logging
import traceback
import types
from typing import Optional

from pydantic import BaseModel

from camera360.lib.camera.protocol import CameraProtocol
from camera360.lib.rpc.connection import MethodCall, MethodReturn


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
        handler: Optional[CameraProtocol],
    ):
        self.reader = reader
        self.writer = writer
        self.handler = handler

        # todo: rename to is_connected or somthing like that
        self._is_dead = False

        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}

        self._loop = asyncio.create_task(self._receive_messages_loop())

    async def _receive_messages_loop(self):
        while True:
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

    async def data_received(self, raw_message: bytes) -> None:
        message = Message.parse_raw(raw_message)

        if (
            message.response_id is not None
            and message.response_id not in self._pending_requests
        ):
            logging.warning("Response id {} not expected".format(message.request_id))
            return

        if message.response_id is not None:
            rpc_response = MethodReturn.parse_raw(message.payload)

            if rpc_response.type == "yield":
                if not self._pending_requests[message.response_id].done():
                    iterator = Iterator()
                    self._pending_requests[message.response_id].set_result(iterator)
                else:
                    iterator = self._pending_requests[message.response_id].result()

                await iterator.put(rpc_response.value)
            elif rpc_response.type == "stop_iteration":
                iterator = self._pending_requests[message.response_id].result()
                await iterator.put(StopAsyncIteration())
                del self._pending_requests[message.response_id]
            else:
                # getting metadata of the methods to be able to unpack payload
                self._pending_requests.pop(
                    message.response_id
                ).set_result(
                    rpc_response.value
                )
        else:
            logging.info("Got request with id {}".format(message.request_id))

            tcp_data = MethodCall.parse_raw(message.payload)

            # getting metadata of the methods to be able to unpack payload
            if self.handler is None:
                return

            method_meta = self.handler.methods[tcp_data.method]
            arguments = method_meta.args_model.parse_raw(tcp_data.arguments)

            # actually executing what we have in handler
            try:
                method = getattr(self.handler, tcp_data.method)(**arguments.dict())
            except:
                traceback.print_exc()
                raise

            if isinstance(method, types.AsyncGeneratorType):
                raise NotImplementedError
            else:
                response = await method
                if method_meta.return_model:
                    response_raw = (
                        method_meta.return_model(value=response)
                        .model_dump_json()
                        .encode()
                    )
                else:
                    response_raw = None

                if response_raw:
                    logging.info(
                        "Request id={} response={}".format(
                            message.request_id, response_raw[:50])
                    )
                else:
                    logging.info('Request id={} finished'.format(message.request_id))

                await self.send_response(
                    message.request_id,
                    MethodReturn(value=response_raw, type="return")
                    .model_dump_json()
                    .encode(),
                )
