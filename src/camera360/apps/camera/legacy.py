import typing

from camera360.lib.camera import device
from camera360.lib.camera.controls import (
    BaseControl,
    MenuItem,
    Integer
)
from camera360.lib.camera.protocol import Metadata
from camera360.lib.supervisor.protocol import FrameData


class FakeAPI(device.API):
    def __init__(self):
        pass

    async def metadata(self) -> Metadata:
        return Metadata(devices=[])

    async def controls(self) -> typing.List[BaseControl]:
        return [
            MenuItem(name='Test patterns', options=['Vertical Bars', 'Horizontal', 'c'], control_type='menu_item'),
            Integer(name='Frequency', minimum=10, maximum=25, default=1),
            Integer(name='Exposure', minimum=10, maximum=25, default=1),
            Integer(name='Vertical Bars', minimum=10, maximum=25, default=1)
        ]

    async def get_frame(self) -> FrameData:
        return FrameData(index=1, frame=b'')
