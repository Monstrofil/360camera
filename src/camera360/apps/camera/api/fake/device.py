import typing
from pathlib import Path

from camera360.lib.camera import device
from camera360.lib.camera.controls import BaseControl, MenuItem, Integer
from camera360.lib.camera.device import RawFrame
from camera360.lib.camera.protocol import Metadata


class FakeDevice(device.API):
    def __init__(self):
        self._frame_index = 0

    async def metadata(self) -> Metadata:
        return Metadata(devices=[])

    async def controls(self) -> typing.List[BaseControl]:
        return [
            MenuItem(
                name="Test patterns",
                options=["Vertical Bars", "Horizontal", "c"],
                control_type="menu_item",
            ),
            Integer(name="Frequency", minimum=10, maximum=25, default=1),
            Integer(name="Exposure", minimum=10, maximum=25, default=1),
            Integer(name="Vertical Bars", minimum=10, maximum=25, default=1),
        ]

    async def get_frame(self) -> RawFrame:
        base_dir = Path(__file__).parent.absolute()

        with open(base_dir / "test.jpg", "rb") as f:
            return RawFrame(sequence=self._frame_index + 1, buffer=f.read())
