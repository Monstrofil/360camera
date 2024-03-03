import logging
import typing
from functools import partial


from camera360.lib.rpc.connection.channel import Channel
from camera360.lib.rpc.connection import MethodCall
from camera360.lib.rpc.decorators import MethodType
from camera360.lib.rpc.protocol import RPCProtocol

T = typing.TypeVar("T")


class RemotePython(typing.Generic[T]):
    def __init__(self, protocol: T, channel: Channel):
        self._protocol: RPCProtocol = protocol
        self._channel: Channel = channel

        for name, member in self._protocol.methods.items():
            logging.debug("Processing method %s", member)

            # copying methods from the protocol but overriding them with remote call logic
            self.__dict__[name] = partial(self._call_remote_method, member, name)

    def __repr__(self):
        return f"RemotePython[{self._protocol.__name__}] at {hex(id(self))}"

    async def _call_remote_method(
        self,
        member: MethodType,
        method_name: str,
        **arguments,
    ):
        payload = member.args_model(**arguments)

        response = await self._channel.send_request(
            MethodCall(method=method_name, arguments=payload.model_dump_json().encode())
            .model_dump_json()
            .encode()
            + b"\n"
        )

        return member.return_model.model_validate_json(response).value
