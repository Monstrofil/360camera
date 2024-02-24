import asyncio
import datetime
import logging
from typing import Optional

from camera360.apps.camera.api import CameraAPI
from camera360.lib.camera.protocol import CameraProtocol, CaptureStartData
from camera360.lib.supervisor.protocol import SupervisorProtocol
from camera360.lib.rpc.server import start_server


class Handler(CameraProtocol):
    def __init__(self):
        self.clients: list[SupervisorProtocol] = []

        self._camera_api = CameraAPI()

        self._capture_task: Optional[asyncio.Task] = None

    async def metadata(self):
        return await self._camera_api.metadata()

    async def start(
        self, *, device_id: int, width: int, height: int
    ) -> CaptureStartData:
        if self._capture_task:
            raise RuntimeError("Already started.")

        await self._camera_api.start(width=width, height=height)
        self._capture_task = asyncio.create_task(self._capture_loop())
        return CaptureStartData(
            capture_time=datetime.datetime.now(), index=1, meta=dict(test="test")
        )

    async def _capture_loop(self) -> None:
        while True:
            frame = await self._camera_api.get_frame()

            logging.info("Sending frame callback")
            await asyncio.gather(
                *[item.on_frame_received(frame=frame) for item in self.clients]
            )
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        await self._camera_api.stop()

        self._capture_task.cancel()


async def run():
    handler = Handler()

    await start_server(handler, host="0.0.0.0", port=8000)


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(run())


if __name__ == "__main__":
    main()
