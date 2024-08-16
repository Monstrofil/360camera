import asyncio
import base64
import dataclasses
import datetime
import logging
import traceback
import typing
import uuid
from dataclasses import dataclass
from pathlib import Path

from camera360.apps.camera.api import load_api
from camera360.apps.camera.settings import settings
from camera360.lib.camera.protocol import (
    CameraProtocol,
    CaptureStartData,
    CaptureStatusData,
    CameraStatus,
    FinishedRecording,
    CaptureStatistics
)
from camera360.lib.rpc.protocol import RPCHandler
from camera360.lib.supervisor.protocol import SupervisorProtocol, FrameData
from camera360.lib.transport.http import start_server
from functools import partial
from camera360.lib.camera.controls import AnyControl


@dataclass
class Capture:
    task: asyncio.Task

    statistics: CaptureStatistics = dataclasses.field(default_factory=CaptureStatistics)


class Handler(RPCHandler, CameraProtocol):
    def __init__(self):
        self.supervisors: list[SupervisorProtocol] = []

        self._api = load_api(settings.device)
        self._factory = self._api.Factory()

        self._capture_tasks: dict[str, Capture] = {}
        self._handler_id = uuid.uuid4().hex
        super().__init__()

    async def id(self):
        return self._handler_id

    async def devices(self):
        return await self._factory.list_devices()

    async def metadata(self):
        return await self._factory.metadata()

    async def captures(self):
        recording_path = Path(settings.storage_path) / self._handler_id
        return await self._factory.list_captures(str(recording_path))

    async def start(
            self, *, device_path: str, width: int, height: int
    ) -> CaptureStartData:
        if device_path in self._capture_tasks:
            raise RuntimeError("Already started.")

        camera_api = self._api.Device(device_path)
        encoder = self._api.Encoder()

        recording_path = Path(settings.storage_path) / self._handler_id / datetime.datetime.now().isoformat()

        await encoder.init(destination=str(recording_path), width=width, height=height)
        await camera_api.start(width=width, height=height)

        task = asyncio.create_task(self._capture_loop(camera_api, encoder, device_path))
        self._capture_tasks[device_path] = Capture(task=task)
        task.add_done_callback(partial(self.on_task_done, device_path))

        try:
            # check that we really start capture
            # because actual stream can just hang
            # and never give us any frames
            await asyncio.wait_for(
                camera_api.frame_received_event.wait(),
                timeout=1
            )
        except asyncio.TimeoutError:
            logging.error('Timed out waiting for frame received. Camera is not started properly.')
            raise

        return CaptureStartData(
            index=1,
            capture_time=datetime.datetime.now(),
            recording_path=str(recording_path)
        )

    def on_task_done(self, device_path: str, future: asyncio.Future):
        if e := future.exception():
            traceback.print_exception(e)

    async def _capture_loop(self, camera_api, encoder, device_path) -> None:
        try:
            async for frame in camera_api.get_frame():
                await encoder.encode(frame)

                self._capture_tasks[device_path].statistics.frames += 1
        except asyncio.CancelledError:
            logging.info('Capture loop is being cancelled')
            await camera_api.stop()
            await encoder.fini()

    async def stop(self, device_path: str) -> FinishedRecording | None:
        if device_path not in self._capture_tasks:
            logging.warning("Camera already stopped")
            return

        self._capture_tasks[device_path].task.cancel()
        while True:
            try:
                await asyncio.wait_for(self._capture_tasks[device_path].task, timeout=1)
            except asyncio.TimeoutError:
                self._capture_tasks[device_path].task.cancel()
            else:
                break

        recording = FinishedRecording(
            statistics=self._capture_tasks[device_path].statistics
        )
        del self._capture_tasks[device_path]

        return recording

    async def status(self, *, device_path: str) -> CaptureStatusData:
        if device_path not in self._capture_tasks:
            return CaptureStatusData(status=CameraStatus.IDLE, frame=None)

        return CaptureStatusData(
            status=CameraStatus.BUSY,
            frame=self._capture_tasks[device_path].statistics.frames
        )

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
