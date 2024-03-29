import logging
import importlib
from dataclasses import dataclass

from camera360.lib.camera import device


@dataclass
class Api:
    Device: type[device.VideoDevice]
    Encoder: type[device.Encoder]
    Preview: type[device.Encoder]


def load_api(name: str) -> Api:
    logging.info('Loading api = %s', name)
    return importlib.import_module(f'.{name}', package=__package__)
