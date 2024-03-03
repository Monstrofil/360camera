import logging
from typing import Optional

from v4l2py import Device

from camera360.apps.camera.rockchip import iter_media_devices, get_media_device
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
        self.frame_id: int = 0

    async def metadata(self) -> Metadata:
        return Metadata(
            devices=[
                Camera(name=device.sensor_name, path=device.media_device, modes=[])
                for device in iter_media_devices()
            ]
        )

    async def start(self, path: str, width: int, height: int):
        rockchip_media = get_media_device(media_device_path=path)

        self._video_device = Device(rockchip_media.mainpath_device, read_write=True)
        self._video_device.open()

        self._controls_device = Device(rockchip_media.sensor_device, read_write=True)
        self._controls_device.open()

    async def controls(self):
        if self._controls_device is None:
            return None

        return ["MenuControl" for control in self._controls_device.controls.values()]

    async def stop(self):
        self._video_device.close()
        self._controls_device.close()

    async def get_frame(self) -> FrameData:
        frame = self._video_device.get_image()
        logging.info("Got frame %s", frame.get_buffer().length)

        self.frame_id = self.frame_id + 1
        return FrameData(index=self.frame_id, frame=b"")
