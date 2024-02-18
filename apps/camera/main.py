import asyncio
import datetime
import logging
from typing import Generator

from lib.camera.protocol import ServerProtocol, CaptureStartData, FrameData
from lib.rpc.server import start_server


class CameraAPI:
    pass


class Handler(ServerProtocol):
    def __init__(self):
        super().__init__()

        self._camera_api = CameraAPI()
        self._is_capture_started = False

    async def start(self, *, device_id: int) -> CaptureStartData:
        if self._is_capture_started:
            raise RuntimeError("Already started.")

        return CaptureStartData(
            capture_time=datetime.datetime.now(), index=1, meta=dict(test="test")
        )

    async def iter_frames(self) -> Generator[FrameData, None, None]:
        # if not self._is_capture_started:
        #     raise RuntimeError("Capture not started")

        for i in range(10):
            yield FrameData(index=i)
            await asyncio.sleep(0.1)


async def main():
    handler = Handler()

    await start_server(handler)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(main())
