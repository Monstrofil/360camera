import asyncio
import base64
import datetime
import logging
import traceback
import typing
import uuid
from pathlib import Path

from camera360.apps.camera.api import load_api
from camera360.apps.camera.settings import settings
from camera360.lib.camera.protocol import CameraProtocol, CaptureStartData
from camera360.lib.rpc.protocol import RPCHandler
from camera360.lib.supervisor.protocol import SupervisorProtocol, FrameData
from camera360.lib.transport.http import start_server
from functools import partial
from camera360.lib.camera.controls import AnyControl


class Handler(RPCHandler, CameraProtocol):
    def __init__(self):
        self.supervisors: list[SupervisorProtocol] = []
        
        self._api = load_api(settings.device)
        self._factory = self._api.Factory()

        self._capture_tasks: dict[str, asyncio.Task] = {}
        self._handler_id = uuid.uuid4().hex
        super().__init__()

    async def id(self):
        return self._handler_id

    async def devices(self):            
        return await self._factory.list_devices()

    async def metadata(self):
        return await self._factory.metadata()

    async def start(
        self, *, device_path: str, width: int, height: int
    ) -> CaptureStartData:
        if device_path in self._capture_tasks:
            raise RuntimeError("Already started.")
        
        camera_api = self._api.Device(device_path)
        encoder = self._api.Encoder()

        recording_path = Path(settings.storage_path) / self._handler_id

        await encoder.init(destination=str(recording_path), width=width, height=height)
        await camera_api.start(width=width, height=height)

        task = asyncio.create_task(self._capture_loop(camera_api, encoder))
        self._capture_tasks[device_path] = task
        task.add_done_callback(partial(self.on_task_done, device_path))

        return CaptureStartData(
            capture_time=datetime.datetime.now(),
            index=1,
            meta=dict(test="test")
        )

    def on_task_done(self, device_path: str, future: asyncio.Future):
        del self._capture_tasks[device_path]
        if e := future.exception():
            traceback.print_exception(e)

    async def _send_frame_callback(self, frame: FrameData):
        logging.info("Sending frame callback")
        try:
            await asyncio.gather(
                *[
                    item.on_frame_received(frame=frame)
                    for item in self.supervisors
                ]
            )
        except ConnectionResetError:
            logging.warning("Unable to deliver callback")
            pass

    async def _capture_loop(self, camera_api, encoder) -> None:
        try:
            async for frame in camera_api.get_frame():
                await encoder.encode(frame)
                await self._send_frame_callback(FrameData(index=frame.sequence))
        except asyncio.CancelledError:
            logging.info('Capture loop is being cancelled')
            await camera_api.stop()
            await encoder.fini()

    async def stop(self, device_path: str) -> None:
        if device_path not in self._capture_tasks:
            logging.warning("Camera already stopped")
            return

        self._capture_tasks[device_path].cancel()

    async def reset(self) -> None:
        if self._capture_task:
            await self.stop()

    async def preview(self, device_path: str) -> bytes:
        camera_api = self._api.Device(device_path)
        preview_encoder = self._api.Preview()

        await preview_encoder.init(640, 480)
        await camera_api.start(640, 480)
        try:
            async for frame in camera_api.get_frame(frames=1):
                try:
                    jpeg_bytes = await preview_encoder.encode(frame)
                    return base64.encodebytes(jpeg_bytes)
                except FileNotFoundError:
                    await asyncio.sleep(0.2)
        finally:
            await camera_api.stop()

    async def controls(self, *, device_path) -> list[AnyControl]:
        camera_api = self._api.Device(device_path)
        return await camera_api.controls()
    
    async def set_control(self, *, device_path: str, control_name: str, value: typing.Any):
        camera_api = self._api.Device(device_path)
        logging.info('Set control %s value %s', control_name, value)
        await camera_api.set_control(control_name=control_name, value=value)



def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    handler = Handler()
    start_server(handler, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
