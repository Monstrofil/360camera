from pydantic import BaseModel

from camera360.lib.rpc.protocol import RPCProtocol, method


class FrameData(BaseModel):
    index: int
    frame: bytes


class SupervisorProtocol(RPCProtocol):
    @method
    async def on_frame_received(self, *, frame: FrameData) -> None:
        ...
