import asyncio
import datetime
import logging
import os
import shlex
import typing


class FakeEncoder:
    def __init__(self, dirname="video"):
        self._dirname = dirname
        self._capture_pipeline: typing.Optional[asyncio.subprocess.Process] = None

    async def init(self):
        os.makedirs(self._dirname, exist_ok=True)

        self._capture_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                "! image/jpeg, width=378, height=378 "
                "! jpegdec "
                "! video/x-raw, framerate=10/1 "
                "! x264enc "
                "! h264parse "
                "! mp4mux "
                f"! filesink location={self._dirname}/{datetime.datetime.now().isoformat()}.mp4"
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
