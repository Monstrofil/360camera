import asyncio
import datetime
import logging
import os
import shlex
import typing

from camera360.lib.camera import device


class MppEncoder(device.Encoder):
    """
    This encoder is specific for RockChip systems
    because it uses hardware accelerated mpph264enc
    which is not available on other systems.

    And wise-versa, generic encoders are not
    available (or at least not hardware-accelerated)
    on rockchip systems.
    """
    def __init__(self, dirname="video"):
        self._dirname = dirname
        self._capture_pipeline: typing.Optional[asyncio.subprocess.Process] = None

    async def init(self):
        os.makedirs(self._dirname, exist_ok=True)

        self._capture_pipeline = await asyncio.create_subprocess_exec(
            "gst-launch-1.0",
            *shlex.split(
                "fdsrc fd=0 "
                '! queue '
                '! rawvideoparse width=4048 height=3040 format=nv12 framerate=10/1 '
                '! mpph264enc '
                '! h264parse '
                '! mp4mux '
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
