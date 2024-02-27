import logging
import typing
from functools import partial


from camera360.lib.rpc.connection.channel import Channel, Iterator
from camera360.lib.rpc.connection import MethodCall
from camera360.lib.rpc.decorators import MethodType


T = typing.TypeVar("T")


class Executor(typing.Generic[T]):
    def __init__(self, protocol: T, channel: Channel):
        self._protocol = protocol
        self._channel = channel

        for name, member in self._protocol.methods.items():
            logging.debug("Processing method %s", member)

            # copying methods from the protocol but overriding them with remote call logic
            self.__dict__[name] = partial(self._call_remote_method, member, name)

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

        if member.return_model is None:
            return None

        if isinstance(response, Iterator):
            return (
                member.return_model.parse_raw(item).value async for item in response
            )
        return member.return_model.parse_raw(response).value
