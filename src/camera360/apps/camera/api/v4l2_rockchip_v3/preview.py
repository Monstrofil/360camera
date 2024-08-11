import asyncio
import logging
import shlex
import typing
from dataclasses import dataclass

from camera360.lib.camera.device import RawFrame


@dataclass
class EncodeFormat:
    width: int
    height: int


class PreviewEncoder:
    def __init__(self):
        self._preview_pipeline: typing.Optional[asyncio.subprocess.Process] = None

        self._encode_format: EncodeFormat | None = None

    async def init(self, width: int, height: int, framerate: int = 10):
        self._preview_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                '! queue '
                f'! rawvideoparse width={width} height={height} format=nv12 framerate={framerate}/1 '
                '! jpegenc '
                "! filesink location=raw.jpeg"
            ),
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )
        self._encode_format = EncodeFormat(width, height)

    async def fini(self):
        if self._preview_pipeline:
            self._preview_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')
        await self._preview_pipeline.wait()
        self._preview_pipeline = None
        self._encode_format = None

    async def encode(self, frame: RawFrame) -> bytes:
        assert frame.width == self._encode_format.width, \
            f"{frame.width} != {self._encode_format.width}"
        assert frame.height == self._encode_format.height, \
            f"{frame.height} != {self._encode_format.height}"

        logging.info("Enconding buffer len=%s", len(frame.buffer))
        self._preview_pipeline.stdin.write(frame.buffer)
        await self._preview_pipeline.stdin.drain()
        self._preview_pipeline.stdin.close()

        # jpeg_data = await self._preview_pipeline.stdout.read()
        await self._preview_pipeline.wait()
        with open('raw.jpeg', 'rb') as f:
            jpeg_data = f.read()

        return jpeg_data
