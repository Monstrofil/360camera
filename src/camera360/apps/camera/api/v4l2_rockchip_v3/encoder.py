import asyncio
import datetime
import io
import logging
import os
import pathlib
import shlex
import struct
import typing
from dataclasses import dataclass

from camera360.lib.camera import device


@dataclass
class EncodeFormat:
    width: int
    height: int


# id: uint16
# timestamp: uint32
# sequence: uint32
METADATA_PACKET_FRAME = struct.Struct('HfI')



class FakeEncoder(device.Encoder):

    def __init__(self):
        self._capture_pipeline: typing.Optional[asyncio.subprocess.Process] = None
        # todo: probably this must be a part of another class
        self._metadata_file: typing.Optional[io.BytesIO] = None

        self._encode_format: EncodeFormat | None = None

    async def init(self, destination: str, width: int, height: int, framerate=10) -> None:
        os.makedirs(destination, exist_ok=True)
        self._encode_format = EncodeFormat(width, height)

        location = pathlib.Path(destination)
        self._capture_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                '! queue '
                f'! rawvideoparse width={width} height={height} format=nv12 framerate={framerate}/1 '
                '! mpph264enc '
                '! h264parse '
                '! mp4mux '
                f"! filesink location={location.with_suffix('.mp4')}"
            ),
            stdin=asyncio.subprocess.PIPE
        )
        self._metadata_file = location.with_suffix('.metadata').open('wb')

    async def fini(self):
        if self._capture_pipeline:
            self._capture_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')

        await self._capture_pipeline.wait()
        self._capture_pipeline = None
        self._encode_format = None

        self._metadata_file.close()
        self._metadata_file = None

    async def encode(self, frame: device.RawFrame):
        logging.info("Encoding buffer")

        assert frame.width == self._encode_format.width, \
            f"{frame.width} != {self._encode_format.width}"
        assert frame.height == self._encode_format.height, \
            f"{frame.height} != {self._encode_format.height}"

        self._capture_pipeline.stdin.write(frame.buffer)
        await self._capture_pipeline.stdin.drain()

        self._metadata_file.write(
            METADATA_PACKET_FRAME.pack(0x01, frame.timestamp, frame.sequence)
        )
