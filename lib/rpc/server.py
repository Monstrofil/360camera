import asyncio
import logging

from .connection.channel import Channel
from .connection import MethodCall, MethodReturn
from .decorators import SerializableMixin


async def handle_client(
    handler: SerializableMixin,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
):
    while not reader.at_eof():
        payload = await reader.readline()
        if not payload:
            continue

        logging.debug("Received request %s", payload)
        tcp_data = MethodCall.parse_raw(payload)

        # getting metadata of the methods to be able to unpack payload
        method_meta = getattr(handler.metadata, tcp_data.method)
        arguments = method_meta.args_model.parse_raw(tcp_data.arguments)

        # actually executing what we have in handler
        method = getattr(handler, tcp_data.method)(**arguments.dict())

        try:
            if method_meta.streaming:
                async for result in method:
                    logging.info(
                        "Function `%s`(**%s) yield: `%s`",
                        tcp_data.method,
                        repr(arguments.dict()),
                        result,
                    )

                    writer.write(
                        MethodReturn(value=result, type="yield")
                        .model_dump_json()
                        .encode()
                        + b"\n"
                    )
                    await writer.drain()
                writer.write(
                    MethodReturn(value=None, type="stop_iteration")
                    .model_dump_json()
                    .encode()
                    + b"\n"
                )
            else:
                result = await method

                logging.info(
                    "Function `%s`(**%s) return: `%s`",
                    tcp_data.method,
                    repr(arguments.dict()),
                    result,
                )

                writer.write(
                    MethodReturn(value=result).model_dump_json().encode() + b"\n"
                )
        except Exception as e:
            writer.write(
                MethodReturn(value=str(e), type="error").model_dump_json().encode()
                + b"\n"
            )

    logging.info("Client disconnected")
    writer.close()
    await writer.wait_closed()


async def start_server(handler, host: str = "127.0.0.1", port: int = 8000):
    _channels: dict[tuple[str, int], Channel] = dict()

    async def create_channel(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer = writer.transport.get_extra_info("peername")

        if peer in _channels:
            raise RuntimeError("Channel already exists")

        _channels[peer] = Channel(reader, writer, handler)

    server = await asyncio.start_server(
        host=host, port=port, client_connected_cb=create_channel
    )

    async with server:
        await server.serve_forever()
