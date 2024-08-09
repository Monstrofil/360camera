import asyncio
import logging
import os
import shlex
import typing


class PreviewEncoder:
    def __init__(self):
        self._preview_pipeline: typing.Optional[asyncio.subprocess.Process] = None

    async def init(self):
        self._preview_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                '! queue '
                '! rawvideoparse width=4048 height=3040 format=nv12 framerate=10/1 '
                '! jpegenc '
                "! filesink location=raw.jpeg"
            ),
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

    async def fini(self):
        if self._preview_pipeline:
            self._preview_pipeline.stdin.close()

        logging.info('Waiting for the capture process to finish')
        await self._preview_pipeline.wait()
        self._preview_pipeline = None

    async def encode(self, buffer: bytes) -> bytes:
        logging.info("Enconding buffer len=%s", len(buffer))
        self._preview_pipeline.stdin.write(buffer)
        await self._preview_pipeline.stdin.drain()
        self._preview_pipeline.stdin.close()

        # jpeg_data = await self._preview_pipeline.stdout.read()
        await self._preview_pipeline.wait()
        with open('raw.jpeg', 'rb') as f:
            jpeg_data = f.read()

        return jpeg_data
