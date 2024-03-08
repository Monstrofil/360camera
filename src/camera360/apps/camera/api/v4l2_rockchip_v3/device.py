import logging
from typing import Optional

from v4l2py import Device, VideoCapture
from v4l2py.device import BufferType, Frame

from camera360.lib.camera.device import RawFrame
from .rockchip import iter_media_devices, get_media_device
from camera360.lib.camera import device
from camera360.lib.camera.protocol import Metadata, Camera
from camera360.lib.supervisor.protocol import FrameData


class CameraAPI(device.API):
    def __init__(self):
        # with Device.from_id(11, legacy_controls=True) as device:
        #     info: Info = device.info
        #     # print(device.get_format(BufferType.VIDEO_CAPTURE_MPLANE))
        #     # print('controls', device.controls)
        #     # for control in device.controls:
        #     #     print(control)
        self._video_device: Optional[Device] = None
        self._controls_device: Optional[Device] = None
        self._video_feed: Optional[VideoCapture] = None
        self.frame_id: int = 0

    async def metadata(self) -> Metadata:
        return Metadata(
            devices=[
                Camera(name=device.sensor_name, path=device.media_device, modes=[])
                for device in iter_media_devices()
            ]
        )

    async def start(self, path: str, width: int, height: int):
        path = '/dev/media1'
        rockchip_media = get_media_device(media_device_path=path)

        self._video_device = Device(rockchip_media.mainpath_device, read_write=True)
        self._video_device.open()

        self._controls_device = Device(rockchip_media.sensor_device, read_write=True)
        self._controls_device.open()

        self._video_feed = VideoCapture(
            device=self._video_device,
            buffer_type=BufferType.VIDEO_CAPTURE_MPLANE
        )
        self._video_feed.open()

    async def controls(self):
        if self._controls_device is None:
            return None

        return ["MenuControl" for control in self._controls_device.controls.values()]

    async def stop(self):
        self._video_device.close()
        self._controls_device.close()

    async def get_frame(self) -> RawFrame:
        frame: Frame = self._video_feed.buffer.read()
        logging.info(f"Received frame "
                     f"timestamp={frame.timestamp}, "
                     f"frame_nb={frame.frame_nb}, "
                     f"width={frame.width}, "
                     f"height={frame.height}, "
                     f"format={frame.pixel_format.name}")

        if frame.frame_nb != self.frame_id + 1:
            logging.warning('Dropped frame number=%s', self.frame_id + 1)

        self.frame_id = frame.frame_nb
        return RawFrame(sequence=self.frame_id, buffer=frame.data)
