import subprocess


def set_v4l2_media_ctl(device: str, entity_name: str, width: int, height: int, framerate: int = 10):
    # media-ctl --set-v4l2 '"ov5640 0-003c":0 [fmt:<format>/<resolution>@1/<framerate>]'
    subprocess.check_call([
        'media-ctl',
        '-d', device,
        '--set-v4l2', f'"{entity_name}":0 [fmt:SRGGB12_1X12/{width}x{height}@1/{framerate}]'])