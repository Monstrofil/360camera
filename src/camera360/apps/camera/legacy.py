import asyncio
import logging
import os
import shlex
import typing
from pathlib import Path

from camera360.lib.camera import device
from camera360.lib.camera.controls import BaseControl, MenuItem, Integer
from camera360.lib.camera.device import RawFrame
from camera360.lib.camera.protocol import Metadata


class PreviewEncoder:
    def __init__(self, dirname: str):
        self._preview_pipeline = None
        self._dirname = dirname

        self._preview_pipeline: typing.Optional[asyncio.subprocess.Process] = None

    async def init(self):
        os.makedirs(self._dirname, exist_ok=True)

        self._preview_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                "! image/jpeg, width=1000, height=1250 "
                "! jpegdec "
                "! video/x-raw, framerate=10/1 "
                "! x264enc "
                "! h264parse "
                f"! hlssink2 "
                f"max-files=5 "
                f"target-duration=5 "
                f"location={self._dirname}/segment%05d.ts "
                f"playlist-location={self._dirname}/preview.m3u8"
            ),
            stdin=asyncio.subprocess.PIPE,
        )

    async def fini(self):
        if self._preview_pipeline:
            self._preview_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')
        await self._preview_pipeline.wait()
        self._preview_pipeline = None

    async def encode(self, buffer: bytes):
        logging.info("Encondign buffer len=%s", len(buffer))
        self._preview_pipeline.stdin.write(buffer)

    async def get_file(self, filename: str):
        with open(os.path.join(self._dirname, filename), "rb") as f:
            return f.read()


class FakeEncoder:
    def __init__(self, dirname="preview"):
        self._dirname = dirname
        self._capture_pipeline: typing.Optional[asyncio.subprocess.Process] = None

    async def init(self):
        os.makedirs(self._dirname, exist_ok=True)

        self._capture_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                "! image/jpeg, width=1000, height=1250 "
                "! jpegdec "
                "! video/x-raw, framerate=10/1 "
                "! x264enc "
                "! h264parse "
                "! mp4mux "
                f"! filesink location={self._dirname}/v1.mp4"
            ),
            stdin=asyncio.subprocess.PIPE,
        )

    async def fini(self):
        if self._capture_pipeline:
            self._capture_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')
        await self._capture_pipeline.wait()
        self._capture_pipeline = None

    async def encode(self, buffer: bytes):
        logging.info("Encondign buffer len=%s", len(buffer))
        self._capture_pipeline.stdin.write(buffer)


class FakeAPI(device.API):
    def __init__(self):
        self._frame_index = 0

    async def metadata(self) -> Metadata:
        return Metadata(devices=[])

    async def controls(self) -> typing.List[BaseControl]:
        return [
            MenuItem(
                name="Test patterns",
                options=["Vertical Bars", "Horizontal", "c"],
                control_type="menu_item",
            ),
            Integer(name="Frequency", minimum=10, maximum=25, default=1),
            Integer(name="Exposure", minimum=10, maximum=25, default=1),
            Integer(name="Vertical Bars", minimum=10, maximum=25, default=1),
        ]

    async def get_frame(self) -> RawFrame:
        base_dir = Path(__file__).parent.absolute()

        with open(base_dir / "test.jpg", "rb") as f:
            return RawFrame(sequence=self._frame_index + 1, buffer=f.read())
