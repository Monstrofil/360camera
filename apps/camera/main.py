import asyncio
import datetime
import logging
from typing import Generator

from apps.camera.api import CameraAPI
from lib.camera.protocol import ServerProtocol, CaptureStartData, FrameData
from lib.rpc.server import start_server


class Handler(ServerProtocol):
    def __init__(self):
        self._camera_api = CameraAPI()
        self._is_capture_started = False

    async def start(self, *, device_id: int) -> CaptureStartData:
        if self._is_capture_started:
            raise RuntimeError("Already started.")

        self._camera_api.start()
        self._is_capture_started = True
        return CaptureStartData(
            capture_time=datetime.datetime.now(), index=1, meta=dict(test="test")
        )

    async def stop(self) -> None:
        self._camera_api.stop()

        self._is_capture_started = False

    async def iter_frames(self) -> Generator[FrameData, None, None]:
        # if not self._is_capture_started:
        #     raise RuntimeError("Capture not started")

        for i in range(10):
            yield FrameData(index=i, frame=b"123")

        # for i in range(101):
        #     frame = self._camera_api.get_frame()
        #     yield FrameData(index=i, frame=bytes(frame.get_buffer().raw[:10]))
        #
        #     await asyncio.sleep(0)


async def main():
    handler = Handler()

    await start_server(handler)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(main())
