import asyncio
import datetime
import logging
import os
import shlex
import typing
from dataclasses import dataclass

from camera360.lib.camera import device


@dataclass
class EncodeFormat:
    width: int
    height: int


class FakeEncoder(device.Encoder):

    def __init__(self, dirname="video"):
        self._dirname = dirname
        self._capture_pipeline: typing.Optional[asyncio.subprocess.Process] = None

        self._encode_format: EncodeFormat | None = None

    async def init(self, width: int, height: int, framerate: int = 10):
        os.makedirs(self._dirname, exist_ok=True)
        self._encode_format = EncodeFormat(width, height)

        self._capture_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                '! queue '
                f'! rawvideoparse width={width} height={height} format=nv12 framerate={framerate}/1 '
                '! mpph264enc '
                '! h264parse '
                '! mp4mux '
                f"! filesink location={self._dirname}/{datetime.datetime.now().isoformat()}.mp4"
            ),
            stdin=asyncio.subprocess.PIPE
        )

    async def fini(self):
        if self._capture_pipeline:
            self._capture_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')

        await self._capture_pipeline.wait()
        self._capture_pipeline = None
        self._encode_format = None

    async def encode(self, frame: device.RawFrame):
        logging.info("Encoding buffer")

        assert frame.width == self._encode_format.width, \
            f"{frame.width} != {self._encode_format.width}"
        assert frame.height == self._encode_format.height, \
            f"{frame.height} != {self._encode_format.height}"

        self._capture_pipeline.stdin.write(frame.buffer)
        await self._capture_pipeline.stdin.drain()
