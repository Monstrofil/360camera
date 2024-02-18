import asyncio
import datetime
import logging

from lib.camera.protocol import ServerProtocol, CaptureStartData
from lib.rpc.server import start_server


class Handler(ServerProtocol):
    async def init(self) -> int:
        return 123123

    async def start(self, *, test_arg: str) -> CaptureStartData:
        return CaptureStartData(
            capture_time=datetime.datetime.now(), index=1, meta=dict(test="test")
        )


async def main():
    handler = Handler()

    await start_server(handler)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(main())
