import glob
import pathlib

from camera360.lib.camera import device

from .rockchip import iter_media_devices
from camera360.lib.camera import device
from camera360.lib.camera.protocol import Metadata, Camera
from ...settings import settings


class Factory(device.Factory):
    def __init__(self):
        ...

    async def list_devices(self) -> list[str]: 
        list_of_media = []
        for device in iter_media_devices():
            list_of_media.append(device.media_device)
            
        return list_of_media

    async def list_captures(self, storage: str) -> list[str]:
        location = pathlib.Path(settings.storage_path) / '*/*.metadata'

        print(location)
        return glob.glob(str(location))
    
    async def metadata(self) -> Metadata:
        return Metadata(
            devices=[
                Camera(name=device.sensor_name, path=device.media_device, modes=[])
                for device in iter_media_devices()
            ]
        )
