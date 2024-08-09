import logging
from typing import Optional

from v4l2py import Device, VideoCapture
from v4l2py.device import BufferType, MenuControl, BaseNumericControl, BooleanControl, Frame

from camera360.lib.camera import controls
from camera360.lib.camera.device import RawFrame
from .rockchip import get_media_device, iter_media_devices
from camera360.lib.camera import device
from camera360.lib.camera.protocol import Metadata, Camera


BUFFERS_COUNT = 4


class CameraAPI(device.VideoDevice):
    def __init__(self, media_path: str):
        self._video_device: Optional[Device] = None
        self._controls_device: Optional[Device] = None

        rockchip_media = get_media_device(media_device_path=media_path)

        self._video_device = Device(rockchip_media.mainpath_device, read_write=True)
        self._video_device.open()

        self._controls_device = Device(rockchip_media.sensor_device, read_write=True)
        self._controls_device.open()

        self._video_feed: Optional[VideoCapture] = None

        self._media_path = media_path
        self.frame_id: int = 0

    async def metadata(self) -> Metadata:
        return Metadata(
            devices=[
                Camera(name=device.sensor_name, path=device.media_device, modes=[])
                for device in iter_media_devices()
            ]
        )

    async def start(self, width: int, height: int):
        self._video_feed = VideoCapture(
            device=self._video_device,
            buffer_type=BufferType.VIDEO_CAPTURE_MPLANE,
            size=BUFFERS_COUNT
        )
        self._video_feed.open()

    async def controls(self) -> list[controls.AnyControl]:
        if self._controls_device is None:
            return []

        all_controls = []
        for v4l_control in self._controls_device.controls.values():
            if isinstance(v4l_control, BaseNumericControl):
                all_controls.append(controls.NumericControl(
                    name=v4l_control.name,
                    value=v4l_control.value,
                    minimum=v4l_control.minimum,
                    maximum=v4l_control.maximum,
                    default=v4l_control.default
                ))
            elif isinstance(v4l_control, MenuControl):
                all_controls.append(controls.MenuItem(
                    name=v4l_control.name,
                    value=v4l_control.value,
                    defaukt=v4l_control.default,
                    options=v4l_control.data,
                ))
            elif isinstance(v4l_control, BooleanControl):
                all_controls.append(controls.BooleanControl(
                    name=v4l_control.name,
                    value=v4l_control.value,
                    default=v4l_control.default
                ))
            else:
                logging.error('Unknown control: %s', v4l_control)

        return all_controls
    
    async def set_control(self, control_name: str, value: int) -> None:
        for v4l_control in self._controls_device.controls.values():
            if v4l_control.name != control_name:
                continue

            logging.info('Changing control %s value to %s', control_name, value)
            v4l_control.value = value
            break
        else:
            raise FileNotFoundError("Control %s does not exist" % control_name)

    async def stop(self) -> None:
        self._video_feed.close()
        self._video_device.close()
        self._controls_device.close()
        
        logging.info('Camera device stopped')

    async def get_frame(self, frames: int | None = None) -> list[RawFrame]:
        # todo: async cycle?
        # async for frame in self._video_feed:

        while frames is None or frames:
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
            yield RawFrame(sequence=self.frame_id, buffer=frame.data)

            frames -= 1
