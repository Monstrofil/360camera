import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from camera360.lib.rpc.server import Connection
from camera360.lib.supervisor.protocol import SystemStatus, SupervisorProtocol


@dataclass
class GlobalStatus:
    status: SystemStatus = SystemStatus.idle
    pending_status: Optional[SystemStatus] = None


class Application:
    def __init__(self):
        self._supervisor: SupervisorProtocol | None = None
        self._status = GlobalStatus()

    async def status(self, refresh: bool = True) -> GlobalStatus:
        if refresh:
            new_status = await self._supervisor.status()
            self._status.status = new_status.status
            self._status.pending_status = new_status.pending_status
        return self._status

    async def start_capture(self):
        assert self._status.status == SystemStatus.idle, \
            "Unable to start already started capture"

        self._status.pending_status = SystemStatus.capture
        await self._supervisor.start()
        await self.status(refresh=True)

    async def stop_capture(self):
        assert self._status.status == SystemStatus.capture, \
            "Unable to start already started capture"

        self._status.pending_status = SystemStatus.idle
        await self._supervisor.stop()
        await self.status(refresh=True)

    async def preview(self, filename):
        return await self._supervisor.preview(filename=filename)

    async def controls(self):
        return await self._supervisor.controls()

    async def set_control(self, name, value):
        return await self._supervisor.set_controls(values={
            name: value
        })

    async def connect(self, reconnect: bool = False):
        connection = Connection(host="127.0.0.1", port=8181)

        self._supervisor = await connection.connect(
            protocol=SupervisorProtocol, handler=None)

        asyncio.ensure_future(self._wait_for_disconnect(connection))

    async def disconnect(self):
        if self._supervisor:
            pass

    async def _wait_for_disconnect(self, connection: Connection):
        logging.info('Client disconnected')
        await connection.wait_for_disconnect()

        while True:
            try:
                await self.connect()
            except ConnectionRefusedError:
                await asyncio.sleep(0.2)
            else:
                break
