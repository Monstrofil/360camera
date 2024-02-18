import asyncio
import json
import logging
import traceback

from lib.camera.protocol import ServerProtocol
from lib.rpc.connection.tcp import TcpPayload


class Handler(ServerProtocol):
    async def init(self) -> int:
        return 123123

    async def start(self, *, test_arg: str) -> str:
        return "Hello World!" + test_arg


async def handle_client(
    handler: Handler, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
):
    while not reader.at_eof():
        payload = await reader.read(1024)
        if not payload:
            continue

        logging.debug("Received response %s", payload)
        tcp_data = TcpPayload.parse_raw(payload)

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
        writer.write(json.dumps(dict(value=result)).encode() + b"\n")

    logging.info("Client disconnected")
    writer.close()
    await writer.wait_closed()


async def main():
    handler = Handler()

    async def client_connected(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            await handle_client(handler, reader, writer)
        except Exception as e:
            traceback.print_exception(e)

    server = await asyncio.start_server(
        host="127.0.0.1", port=8000, client_connected_cb=client_connected
    )

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(main())
