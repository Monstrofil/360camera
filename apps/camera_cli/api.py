import asyncio
import logging

from lib.camera.protocol import ServerProtocol
from lib.rpc.server import connect


async def main():
    executor = await connect(host="127.0.0.1", port=8000, protocol=ServerProtocol)

    method_result = await executor.start(device_id=1)
    print("start", method_result)

    method_result = await executor.iter_frames()
    print(method_result)
    async for result in method_result:
        print("iter", result)

    method_result = await executor.stop()
    print("stop", method_result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)
    asyncio.run(main())
