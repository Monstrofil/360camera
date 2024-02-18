import asyncio
import logging

from lib.camera.protocol import ServerProtocol
from lib.rpc.connection.tcp import TcpConnection
from lib.rpc.executor import Executor


async def main():
    reader, writer = await asyncio.open_connection(host="127.0.0.1", port=8000)
    logging.info("Connection to the server established")

    connection = TcpConnection(reader, writer)
    executor: ServerProtocol = Executor(protocol=ServerProtocol, connection=connection)

    method_result = await executor.start(device_id=1)
    print("start", method_result)

    method_result = await executor.iter_frames()
    print(method_result)
    async for result in method_result:
        print("iter", result)

    method_result = await executor.stop()
    print("stop", method_result)

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
