import asyncio
import base64
import datetime
import logging
import traceback
from typing import Optional

from camera360.apps.camera.legacy import FakeAPI, FakeEncoder, PreviewEncoder
from camera360.apps.camera.settings import settings
from camera360.lib.camera.protocol import CameraProtocol, CaptureStartData
from camera360.lib.rpc.protocol import RPCHandler
from camera360.lib.supervisor.protocol import SupervisorProtocol, FrameData
from camera360.lib.rpc.server import start_server


class Handler(RPCHandler, CameraProtocol):
    def __init__(self):
        self.supervisors: list[SupervisorProtocol] = []

        self._camera_api = FakeAPI()
        self._preview_encoder = PreviewEncoder("preview")
        self._encoder = FakeEncoder()

        self._capture_task: Optional[asyncio.Task] = None
        super().__init__()

    async def metadata(self):
        return await self._camera_api.metadata()

    async def start(
        self, *, device_path: str, width: int, height: int
    ) -> CaptureStartData:
        if self._capture_task:
            raise RuntimeError("Already started.")

        await self._camera_api.start(path=device_path, width=width, height=height)

        self._capture_task = asyncio.create_task(self._capture_loop())
        self._capture_task.add_done_callback(self.on_task_done)

        return CaptureStartData(
            capture_time=datetime.datetime.now(), index=1, meta=dict(test="test")
        )

    def on_task_done(self, future: asyncio.Future):
        if e := future.exception():
            traceback.print_exception(e)

    async def _capture_loop(self) -> None:
        await self._encoder.init()
        await self._preview_encoder.init()

        while True:
            frame = await self._camera_api.get_frame()
            await self._encoder.encode(frame.buffer)
            await self._preview_encoder.encode(frame.buffer)

            logging.info("Sending frame callback")
            try:
                await asyncio.gather(
                    *[
                        item.on_frame_received(frame=FrameData(index=frame.sequence))
                        for item in self.supervisors
                    ]
                )
            except ConnectionResetError:
                logging.warning("Unable to deliver callback")
                pass
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        if self._capture_task is None:
            logging.warning("Camera already stopped")
            return

        await self._camera_api.stop()

        self._capture_task.cancel()
        self._capture_task = None

        await self._encoder.fini()
        await self._preview_encoder.fini()

    async def reset(self) -> None:
        if self._capture_task:
            await self.stop()

    async def preview(self, filename: str) -> bytes:
        try:
            return base64.encodebytes(await self._preview_encoder.get_file(filename))
        except FileNotFoundError:
            return base64.encodebytes(b"#EXTM3U\n"
                    b"#EXT-X-VERSION:3\n"
                    b"#EXT-X-MEDIA-SEQUENCE:0\n"
                    b"#EXT-X-TARGETDURATION:6\n")


async def run():
    handler = Handler()

    server = await start_server(handler, host=settings.host, port=settings.port)

    async with server:
        await server.serve_forever()


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(run())


if __name__ == "__main__":
    main()
