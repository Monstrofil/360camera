import logging
from typing import Optional

import pygame

import pygame.camera

from camera360.lib.camera.protocol import Mode, Metadata
from camera360.lib.supervisor.protocol import FrameData


class CameraAPI:
    def __init__(self):
        self._cam: Optional[pygame.camera.Camera] = None
        self.frame_id: int = 0

        pygame.camera.init()

    async def metadata(self) -> Metadata:
        return Metadata(
            name=pygame.camera.list_cameras()[0],
            modes=[
                Mode(width=640, height=480, bpp=12),
                Mode(width=1024, height=768, bpp=12),
            ],
        )

    async def start(self, width: int, height: int):
        all_webcams = pygame.camera.list_cameras()
        self._cam = pygame.camera.Camera(all_webcams[0], (width, height))
        self._cam.start()

    async def stop(self):
        self._cam.stop()

    async def get_frame(self) -> FrameData:
        frame = self._cam.get_image()
        logging.info("Got frame %s", frame.get_buffer().length)

        self.frame_id = self.frame_id + 1
        return FrameData(index=self.frame_id, frame=b"")
