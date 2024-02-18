import logging

import pygame

import pygame.camera


class CameraAPI:
    def __init__(self):
        pygame.camera.init()

        all_webcams = pygame.camera.list_cameras()
        self._cam = pygame.camera.Camera(all_webcams[0], (640, 480))

    def start(self):
        self._cam.start()

    def stop(self):
        self._cam.stop()

    def get_frame(self):
        frame = self._cam.get_image()
        logging.info('Got frame %s', frame.get_buffer().length)
        pygame.image.save(frame, "photo.png")
        return frame


