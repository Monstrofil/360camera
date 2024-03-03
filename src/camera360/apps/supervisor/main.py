import asyncio
import logging
from contextlib import contextmanager
from typing import List

from camera360.lib.camera.controls import Integer, AnyControl
from camera360.lib.camera.protocol import CameraProtocol
from camera360.lib.rpc.protocol import RPCHandler
from camera360.lib.rpc.server import connect, start_server, Connection
from camera360.lib.supervisor.protocol import (
    SupervisorProtocol,
    FrameData,
    Client,
    Status,
    SystemStatus,
)

CONNECTIONS = [
    ("127.0.0.1", 8000),
    # ("127.0.0.1", 8001)
]


class Handler(RPCHandler, SupervisorProtocol):
    def __init__(self):
        self.supervisors: list[SupervisorProtocol] = []
        self.cameras: list[CameraProtocol] = []

        self._status = Status(status=SystemStatus.idle)
        super().__init__()

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
        print("self.clients", self.supervisors)
        print("self.cameras", self.cameras)
        return [
            Client(name="Camera %s" % index)
            for index, client in enumerate(self.cameras)
        ]

    async def start(self) -> None:
        with self._status_transition(SystemStatus.capture):
            await asyncio.gather(
                *[
                    client.start(device_path="/dev/video0", width=1920, height=1080)
                    for client in self.cameras
                ]
            )

    async def stop(self) -> None:
        with self._status_transition(SystemStatus.idle):
            await asyncio.gather(*[client.stop() for client in self.cameras])

    async def controls(self) -> List[AnyControl]:
        return [
            Integer(name="Exposure", minimum=10, maximum=25, default=1),
        ]

    async def status(self) -> Status:
        self._status.clients = [
            Client(name="Camera %s" % index)
            for index, client in enumerate(self.cameras)
        ]
        return self._status

    async def preview(self, *, filename: str) -> bytes:
        return await self.cameras[0].preview(filename=filename)


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

                await remote.reset()
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


async def run(connections):
    handler = Handler()

    executors = await connect_hosts(connections, handler=handler)

    results = await asyncio.gather(*[api.metadata() for api in executors])
    print("metadata", results)

    handler.cameras = executors

    server = await start_server(handler, host="127.0.0.1", port=8181)

    async with server:
        await server.serve_forever()


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(run(connections=CONNECTIONS))


if __name__ == "__main__":
    main()
