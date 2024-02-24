import asyncio
import logging

from camera360.lib.camera.protocol import CameraProtocol
from camera360.lib.rpc.server import connect
from camera360.lib.supervisor.protocol import SupervisorProtocol, FrameData

CONNECTIONS = [
    ("127.0.0.1", 8000),
    # ("127.0.0.1", 8001)
]


class Handler(SupervisorProtocol):
    def __init__(self):
        pass

    async def on_frame_received(self, frame: FrameData) -> None:
        print("on_frame_received", frame)


async def connect_hosts(connections, handler):
    pending_connections = connections[:]
    executors = []

    while pending_connections:
        for index, (host, port) in enumerate(pending_connections):
            try:
                executor = await connect(
                    host=host, port=port, protocol=CameraProtocol, handler=handler
                )
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

    results = await asyncio.gather(
        *[api.start(device_id=0, width=640, height=480) for api in executors]
    )
    print("start", results)

    await asyncio.sleep(30)

    results = await asyncio.gather(*[api.stop() for api in executors])
    print("stop", results)


def main():
    logging.basicConfig(level=logging.DEBUG, force=True)

    asyncio.run(run(connections=CONNECTIONS))


if __name__ == "__main__":
    main()
