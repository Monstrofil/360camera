import asyncio
import logging
from contextlib import contextmanager, asynccontextmanager
from typing import List, Any

from camera360.lib.camera.controls import NumericControl, AnyControl, MenuItem
from camera360.lib.camera.protocol import CameraProtocol
from camera360.lib.rpc.protocol import RPCHandler
from camera360.lib.transport.http import connect, start_server, Connection
from camera360.lib.supervisor.protocol import (
    SupervisorProtocol,
    FrameData,
    Client,
    Status,
    SystemStatus,
)

from .settings import settings

CONNECTIONS = [
    ("127.0.0.1", 8000),
    # ("127.0.0.1", 8001)
]

RESOLUTION_CONTROL_ID = "Resolution"


class Handler(RPCHandler, SupervisorProtocol):
    def __init__(self):
        self.supervisors: list[SupervisorProtocol] = []
        self.cameras: list[CameraProtocol] = []

        self._status = Status(status=SystemStatus.idle)

        self._controls = [
            MenuItem(name=RESOLUTION_CONTROL_ID, value=0, options={
                0: '1920x1080',
                1: '640x480',
                2: '4048x3040',
            }),
        ]
        super().__init__()

    def _get_control_by_name(self, name: str) -> AnyControl:
        for control in self._controls:
            if control.name != name:
                continue
            return control

    @contextmanager
    def _status_transition(self, status: SystemStatus):
        assert self._status.pending_status is None, "Pending status is already set"

        self._status.pending_status = status

        try:
            yield
        except:
            self._status.pending_status = None
            raise
        else:
            self._status.status = self._status.pending_status
            self._status.pending_status = None

    async def on_frame_received(self, frame: FrameData) -> None:
        print("on_frame_received", frame)

    async def get_clients(self) -> List[Client]:
        return [
            Client(name="Camera %s" % index)
            for index, client in enumerate(self.cameras)
        ]

    async def start(self) -> None:
        resolution_ctrl = self._get_control_by_name(RESOLUTION_CONTROL_ID)
        width, height = map(int, resolution_ctrl.options[resolution_ctrl.value].split('x'))

        tasks = []
        for camera in self.cameras:
            for device in await camera.devices():
                tasks.append(camera.start(device_path=device, width=width, height=height))

        with self._status_transition(SystemStatus.capture):
            await asyncio.gather(*tasks)

    async def stop(self) -> None:
        tasks = []
        for camera in self.cameras:
            for device in await camera.devices():
                tasks.append(camera.stop(device_path=device))

        with self._status_transition(SystemStatus.idle):
            await asyncio.gather(*tasks)

    async def controls(self) -> list[AnyControl]:
        return self._controls[:]

    async def camera_controls(self) -> dict[str, list[AnyControl]]:
        camera_controls = {}
        for camera in self.cameras:
            for device in await camera.devices():
                camera_controls[f'{await camera.id()}_{device}'] = \
                    await camera.controls(device_path=device)
        return camera_controls

    async def set_controls(self, values: dict[str, Any]) -> None:
        for control in self._controls:
            if control.name not in values:
                continue

            control.value = values[control.name]

    async def _get_camera_by_id(self, identifier: str) -> tuple[str, CameraProtocol] | None:
        for camera in self.cameras:
            for device in await camera.devices():
                if identifier != f'{await camera.id()}_{device}':
                    continue
                return device, camera

    async def set_camera_control(self, camera_id: str, name: str, value: Any) -> None:
        device, camera = await self._get_camera_by_id(camera_id)
        await camera.set_control(device_path=device, control_name=name, value=value)

    async def status(self) -> Status:
        self._status.clients = [
            Client(name="Camera %s" % index)
            for index, client in enumerate(self.cameras)
        ]
        return self._status

    async def preview(self, *, camera_id: str) -> bytes:
        device, camera = await self._get_camera_by_id(camera_id)
        return await camera.preview(device_path=device)


async def connect_hosts(connections, handler):
    pending_connections = connections[:]
    executors = []

    while pending_connections:
        for index, (host, port) in enumerate(pending_connections):
            try:
                connection = Connection(
                    host=host, port=port)
                remote = await connection.connect(
                    protocol=CameraProtocol, handler=handler)

                # todo: remove this
                # await remote.reset()
                executors.append(remote)
            except ConnectionRefusedError:
                logging.info("%s:%d is still unreachable", host, port)
                continue
            else:
                logging.info("Connection to %s:%d established", host, port)
                pending_connections.remove((host, port))
                logging.info("%s more hosts left", len(pending_connections))
    logging.info("All connections established")

    return executors


def run(connections):
    handler = Handler()

    @asynccontextmanager
    async def lifespan(app):
        executors = await connect_hosts(connections, handler=handler)

        results = await asyncio.gather(*[api.metadata() for api in executors])

        handler.cameras = executors

        yield

    start_server(handler, host=settings.host, port=settings.port, lifespan=lifespan)


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    run(connections=CONNECTIONS)


if __name__ == "__main__":
    main()
