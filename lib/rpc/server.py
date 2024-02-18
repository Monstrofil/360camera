import asyncio
import logging
import traceback

from .connection.tcp import RPCRequest, RPCResponse


async def handle_client(
    handler: object, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
):
    while not reader.at_eof():
        payload = await reader.readline()
        if not payload:
            continue

        logging.debug("Received response %s", payload)
        tcp_data = RPCRequest.parse_raw(payload)

        # getting metadata of the methods to be able to unpack payload
        method_meta = getattr(handler.metadata, tcp_data.method)
        arguments = method_meta.args_model.parse_raw(tcp_data.arguments)

        # actually executing what we have in handler
        result = await getattr(handler, tcp_data.method)(**arguments.dict())

        logging.info(
            "Function `%s`(**%s) result: `%s`",
            tcp_data.method,
            repr(arguments.dict()),
            result,
        )

        writer.write(RPCResponse(value=result).model_dump_json().encode() + b"\n")

    logging.info("Client disconnected")
    writer.close()
    await writer.wait_closed()


async def start_server(handler, host: str = "127.0.0.1", port: int = 8000):
    async def client_connected(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            await handle_client(handler, reader, writer)
        except Exception as e:
            traceback.print_exception(e)

    server = await asyncio.start_server(
        host=host, port=port, client_connected_cb=client_connected
    )

    async with server:
        await server.serve_forever()