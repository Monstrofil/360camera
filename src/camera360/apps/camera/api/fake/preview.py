import asyncio
import logging
import os
import shlex
import typing


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
