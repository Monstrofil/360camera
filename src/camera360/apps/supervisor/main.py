import asyncio
import logging
from typing import List

from camera360.lib.camera.protocol import CameraProtocol
from camera360.lib.rpc.server import connect, start_server
from camera360.lib.supervisor.protocol import SupervisorProtocol, FrameData, Client

CONNECTIONS = [
    ("127.0.0.1", 8000),
    # ("127.0.0.1", 8001)
]


class Handler(SupervisorProtocol):
    def __init__(self):
        self.clients: list[SupervisorProtocol] = []
        self.cameras: list[CameraProtocol] = []

    async def on_frame_received(self, frame: FrameData) -> None:
        print("on_frame_received", frame)

    async def get_clients(self) -> List[Client]:
        print(self.clients)
        print(self.cameras)
        return [Client(name='Camera %s' % index)
                for index, client in enumerate(self.cameras)]

    async def start(self) -> None:
        await asyncio.gather(*[client.start(
            device_path='/dev/video0',
            width=1920,
            height=1080
        ) for client in self.cameras])

    async def stop(self) -> None:
        await asyncio.gather(
            *[client.stop() for client in self.cameras])


async def connect_hosts(connections, handler):
    pending_connections = connections[:]
    executors = []

    while pending_connections:
        for index, (host, port) in enumerate(pending_connections):
            try:
                executor = await connect(
                    host=host, port=port, protocol=CameraProtocol, handler=handler
                )
                await executor.reset()
                executors.append(executor)
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

    await start_server(handler, host='127.0.0.1', port=8181)


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(run(connections=CONNECTIONS))


if __name__ == "__main__":
    main()
