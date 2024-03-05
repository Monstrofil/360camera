import glob
import logging
import os
from dataclasses import dataclass

from pyrkaiq.mediactl.libmediactl import struct_media_entity_desc
from pyrkaiq.mediactl.sysctl import get_media_entities
from pyrkaiq.rkaiq.sysctl import getBindedSnsEntNmByVd


@dataclass
class MediaTree:
    media_device: str
    sensor_device: str

    subdev_device: str
    params_device: str
    statistics_device: str
    mainpath_device: str

    sensor_name: str


def mediactl_get_device_name(description: struct_media_entity_desc):
    path = os.path.realpath(
        "/sys/dev/char/%u:%u" % (description.v4l.major, description.v4l.minor)
    )
    device_name = path.rsplit("/", 1)[-1]

    return "/dev/" + device_name


def vl4_get_device_by_name(name: str):
    for device in glob.glob("/sys/class/video4linux/*/name"):
        with open(device, "r") as f:
            dev_name = f.read().strip()

        if dev_name != name:
            continue

        path = os.path.realpath(device)
        device_name = path.rsplit("/", 2)[-2]

        return "/dev/" + device_name


def get_media_device(media_device_path: str):
    entities = get_media_entities(media_device_path)

    isp_subdev = next(
        (entity for entity in entities if entity.name == b"rkisp-isp-subdev"), None
    )
    input_params = next(
        (entity for entity in entities if entity.name == b"rkisp-input-params"), None
    )
    isp_statistics = next(
        (entity for entity in entities if entity.name == b"rkisp-statistics"), None
    )
    isp_mainpath = next(
        (entity for entity in entities if entity.name == b"rkisp_mainpath"), None
    )

    if any(
        (
            isp_subdev is None,
            input_params is None,
            isp_statistics is None,
            isp_mainpath is None,
        )
    ):
        logging.info(
            "Device %s does not match rkisp3.x specification", media_device_path
        )
        return

    logging.info("Device %s matches rkisp3.x specification", media_device_path)
    sensor_name = getBindedSnsEntNmByVd(mediactl_get_device_name(isp_mainpath))

    logging.info("Device is binded to the sensor %s", sensor_name)

    return MediaTree(
        sensor_name=sensor_name,
        sensor_device=vl4_get_device_by_name(sensor_name),
        media_device=media_device_path,
        subdev_device=mediactl_get_device_name(isp_subdev),
        params_device=mediactl_get_device_name(input_params),
        statistics_device=mediactl_get_device_name(isp_statistics),
        mainpath_device=mediactl_get_device_name(isp_mainpath),
    )


def iter_media_devices():
    media_devices = glob.glob("/dev/media*")

    for media_device_path in media_devices:
        device = get_media_device(media_device_path)

        if device is not None:
            yield device
